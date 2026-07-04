#!/usr/bin/env python
"""Lifecycle manager for an on-demand vLLM backend process.

Mirrors the idle-unload behavior of questions/inference_server/model_cache.py
(IDLE_UNLOAD_SECONDS) but for a *separate* vLLM server process, so the GPU is
freed when the model sees no traffic for a configurable window:

  - lazy start:   first request boots the backend and blocks until it is ready
  - idle unload:  a daemon thread stops the backend after IDLE_UNLOAD_SECONDS
                  of no `touch()`, releasing all VRAM (kills the whole process
                  group so the vLLM EngineCore child dies too — a plain SIGTERM
                  to the API server leaks the worker's VRAM)
  - re-wake:      the next request boots it again (compile cache makes this ~1 min)

The backend launch command is fully configurable via env so the same manager
works for Gemma, Qwen, SmolLM, etc.:

  VLLM_BACKEND_CMD   shell command that execs the vLLM server (required for
                     managed mode; e.g. "OPT=1 ./serve_5090.sh spec")
  VLLM_BACKEND_CWD   working dir for the command
  VLLM_BACKEND_HOST  default 127.0.0.1
  VLLM_BACKEND_PORT  default 8200
  IDLE_UNLOAD_SECONDS  default 600 (0 disables idle unload)
  BACKEND_STARTUP_TIMEOUT  default 240 (seconds to wait for readiness)
"""
from __future__ import annotations

import logging
import os
import signal
import socket
import subprocess
import threading
import time
import urllib.request

logger = logging.getLogger(__name__)

_IDLE_CHECK_INTERVAL = 15


class BackendManager:
    def __init__(
        self,
        cmd: str,
        host: str = "127.0.0.1",
        port: int = 8200,
        ready_path: str = "/v1/models",
        idle_seconds: int = 600,
        startup_timeout: int = 240,
        cwd: str | None = None,
        env: dict | None = None,
        expect_model: str | None = None,
    ):
        self.cmd = cmd
        self.expect_model = expect_model
        self.host = host
        self.port = port
        self.ready_url = f"http://{host}:{port}{ready_path}"
        self.idle_seconds = idle_seconds
        self.startup_timeout = startup_timeout
        self.cwd = cwd
        self.env = env
        self.proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._last_access = time.time()
        self._starting = False  # guards the idle thread from reaping a booting backend
        self._idle_thread: threading.Thread | None = None
        if self.idle_seconds and self.cmd:
            self._start_idle_thread()

    # -- probes ------------------------------------------------------------
    def _listening(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex((self.host, self.port)) == 0

    def _ready(self) -> bool:
        # expect_model guards the shared-port case: another registry backend
        # answering on the same port must not count as "ready" for this one.
        try:
            with urllib.request.urlopen(self.ready_url, timeout=3) as r:
                if r.status != 200:
                    return False
                if not self.expect_model:
                    return True
                import json
                data = json.loads(r.read())
                return any(m.get("id") == self.expect_model
                           for m in data.get("data", []))
        except Exception:
            return False

    # -- lifecycle ---------------------------------------------------------
    def touch(self) -> None:
        self._last_access = time.time()

    def ensure_up(self) -> None:
        """Block until the backend is ready, launching it if necessary."""
        self.touch()
        if self._ready():
            return
        with self._lock:
            if self._ready():
                return
            if not self.cmd:
                raise RuntimeError("backend not running and VLLM_BACKEND_CMD unset")
            self._starting = True
            try:
                if self.proc is None or self.proc.poll() is not None:
                    # a not-ready listener on our port with no live managed proc
                    # is an orphan from a previous adapter life — reap it or the
                    # new launch dies on bind and its VRAM leaks
                    if self._listening():
                        self._kill_port_orphans()
                    logger.info("Launching vLLM backend: %s", self.cmd)
                    # start_new_session => own process group; we kill the group on stop
                    self.proc = subprocess.Popen(
                        self.cmd, shell=True, cwd=self.cwd, env=self.env,
                        start_new_session=True,
                    )
                deadline = time.time() + self.startup_timeout
                while time.time() < deadline:
                    if self.proc.poll() is not None:
                        raise RuntimeError(
                            f"backend exited during startup (code {self.proc.returncode})")
                    if self._ready():
                        logger.info("vLLM backend ready on %s:%s", self.host, self.port)
                        self.touch()
                        return
                    self.touch()  # keep alive during a long (compile) boot
                    time.sleep(2)
                raise RuntimeError(f"backend not ready within {self.startup_timeout}s")
            finally:
                self._starting = False

    def _kill_port_orphans(self) -> None:
        try:
            out = subprocess.run(
                ["lsof", "-t", f"-iTCP:{self.port}", "-sTCP:LISTEN"],
                capture_output=True, text=True, timeout=10).stdout.split()
        except Exception:
            out = []
        for pid in out:
            try:
                pgid = os.getpgid(int(pid))
                logger.warning("Killing orphan pid %s (pgid %s) on port %s",
                               pid, pgid, self.port)
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, ValueError, PermissionError):
                pass
        for _ in range(30):
            if not self._listening():
                return
            time.sleep(1)
        logger.warning("Port %s still occupied after orphan kill", self.port)

    def stop(self) -> None:
        with self._lock:
            if self.proc is None or self.proc.poll() is not None:
                self.proc = None
                return
            logger.info("Idle-unloading vLLM backend (pid %s) to free GPU", self.proc.pid)
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                self.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            self.proc = None
            # wait for the port to free so a re-wake binds cleanly
            for _ in range(20):
                if not self._listening():
                    break
                time.sleep(0.5)

    # -- idle thread -------------------------------------------------------
    def _start_idle_thread(self) -> None:
        def loop():
            while True:
                time.sleep(_IDLE_CHECK_INTERVAL)
                if self._starting or self.proc is None or self.proc.poll() is not None:
                    continue
                idle = time.time() - self._last_access
                if idle >= self.idle_seconds:
                    logger.info("Backend idle %.0fs >= %ss; unloading", idle, self.idle_seconds)
                    try:
                        self.stop()
                    except Exception as e:  # noqa: BLE001
                        logger.warning("idle stop failed: %r", e)

        self._idle_thread = threading.Thread(target=loop, daemon=True, name="vllm-idle-unload")
        self._idle_thread.start()

    def status(self) -> dict:
        running = self.proc is not None and self.proc.poll() is None
        return {
            "managed": bool(self.cmd),
            "running": running,
            "ready": self._ready(),
            "idle_seconds": self.idle_seconds,
            "seconds_since_last_access": round(time.time() - self._last_access, 1),
            "pid": self.proc.pid if running else None,
        }


def from_env() -> "BackendManager | None":
    """Build a manager from env, or None if managed mode is disabled."""
    cmd = os.environ.get("VLLM_BACKEND_CMD", "").strip()
    if not cmd:
        return None
    return BackendManager(
        cmd=cmd,
        host=os.environ.get("VLLM_BACKEND_HOST", "127.0.0.1"),
        port=int(os.environ.get("VLLM_BACKEND_PORT", "8200")),
        idle_seconds=int(os.environ.get("IDLE_UNLOAD_SECONDS", "600")),
        startup_timeout=int(os.environ.get("BACKEND_STARTUP_TIMEOUT", "240")),
        cwd=os.environ.get("VLLM_BACKEND_CWD") or None,
        env={**os.environ},
        expect_model=os.environ.get("VLLM_MODEL") or None,
    )


class BackendRegistry:
    """One GPU, many models: at most one vLLM backend runs at a time.

    ensure(name) stops whichever other backend is up, then boots the target.
    All backends share a port; expect_model on each manager disambiguates
    readiness. Each manager keeps its own idle-unload thread.
    """

    def __init__(self, managers: dict, default: str):
        if default not in managers:
            raise ValueError(f"default model {default!r} not in registry")
        self.managers = managers
        self.default = default
        self._swap_lock = threading.Lock()

    def resolve(self, name: "str | None") -> str:
        return name if name and name in self.managers else self.default

    def ensure(self, name: "str | None" = None) -> str:
        name = self.resolve(name)
        with self._swap_lock:
            for other_name, other in self.managers.items():
                if other_name != name:
                    if other.proc is not None and other.proc.poll() is None:
                        logger.info("Swapping backend %s -> %s", other_name, name)
                        other.stop()
            self.managers[name].ensure_up()
        return name

    def touch(self, name: "str | None" = None) -> None:
        self.managers[self.resolve(name)].touch()

    def status(self) -> dict:
        return {"default": self.default,
                "models": {n: m.status() for n, m in self.managers.items()}}

    def stop_all(self) -> None:
        for m in self.managers.values():
            m.stop()


def registry_from_env() -> "BackendRegistry | None":
    """Multi-model registry from VLLM_MODELS_JSON, else single-model wrap of
    from_env(), else None (unmanaged proxy mode).

    VLLM_MODELS_JSON example:
      {"qwen3.5-4b": {"cmd": "MODEL=/path SERVED=qwen3.5-4b ./serve_generic.sh"},
       "gemma-4-e4b-it": {"cmd": "...", "startup_timeout": 300}}
    Optional per-model keys: port, idle_seconds, startup_timeout, cwd.
    VLLM_DEFAULT_MODEL picks the default (else first key).
    """
    import json as _json
    spec = os.environ.get("VLLM_MODELS_JSON", "").strip()
    if spec:
        cfg = _json.loads(spec)
        managers = {}
        for name, m in cfg.items():
            if isinstance(m, str):
                m = {"cmd": m}
            managers[name] = BackendManager(
                cmd=m["cmd"],
                host=os.environ.get("VLLM_BACKEND_HOST", "127.0.0.1"),
                port=int(m.get("port", os.environ.get("VLLM_BACKEND_PORT", "8200"))),
                idle_seconds=int(m.get("idle_seconds",
                                       os.environ.get("IDLE_UNLOAD_SECONDS", "600"))),
                startup_timeout=int(m.get("startup_timeout",
                                          os.environ.get("BACKEND_STARTUP_TIMEOUT", "240"))),
                cwd=m.get("cwd") or os.environ.get("VLLM_BACKEND_CWD") or None,
                env={**os.environ},
                expect_model=name,
            )
        default = os.environ.get("VLLM_DEFAULT_MODEL") or next(iter(managers))
        return BackendRegistry(managers, default)
    single = from_env()
    if single is None:
        return None
    name = os.environ.get("VLLM_MODEL", "model")
    return BackendRegistry({name: single}, name)
