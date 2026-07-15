#!/usr/bin/env python3
"""
Inference server monitor with Codex auto-fix agent.

Checks the inference server liveness endpoint every 30 minutes.
If inference is down, spawns a Codex agent to diagnose, fix, redeploy,
and verify the fix.

Usage:
    python monitors/monitor_inference_agent.py
    python monitors/monitor_inference_agent.py --interval 900  # 15 min
    python monitors/monitor_inference_agent.py --once           # single check
"""
import argparse
import fcntl
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "monitors"
LOG_FILE = LOG_DIR / "monitor_inference_agent.log"
CODEX_LOG_FILE = LOG_DIR / "codex_inference_fix.log"
LOCK_FILE = Path("/tmp/text-generator-monitor-inference-agent.lock")
CODEX_LOCAL = os.environ.get("CODEX_LOCAL", "/usr/local/bin/codex")
CODEX_CMD = [
    CODEX_LOCAL,
    "exec",
    "--dangerously-bypass-approvals-and-sandbox",
    "-m",
    "gpt-5.6-sol",
    "--config",
    "model_reasoning_effort=medium",
]

URL_LOCAL = "http://localhost:9080/liveness_check"
# NOTE: deep checks (?deep=1) force a real generation, which cold-booted the
# idle-unloaded vLLM backend every ~3h and "failed" whenever the boot exceeded
# the probe timeout. The shallow endpoint already reports healthy-when-idle,
# so the periodic "deep" probe now uses it too.
URL_LOCAL_DEEP = URL_LOCAL
URL_EXTERNAL = "https://api.text-generator.io/liveness_check"

CHECK_INTERVAL = 1800  # 30 minutes
FAIL_THRESHOLD = 2  # consecutive failures before spawning agent
AGENT_COOLDOWN = 3600  # min seconds between agent invocations
MAX_AGENT_RUNTIME = 600  # 10 min timeout for codex agent
DEEP_CHECK_EVERY_N = 6  # run a real inference check every N cycles (~3 hours)


def log(message: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} {message}"
    with open(LOG_FILE, "a") as fh:
        fh.write(line + "\n")
    print(line)


def check_endpoint(url: str, timeout: int = 30) -> tuple[bool, str]:
    """Check endpoint, return (ok, detail)."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 InferenceMonitor"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
            status_ok = resp.status < 400
            inference_ok = data.get("inference") == "ok"
            if status_ok and inference_ok:
                return True, f"status={resp.status} inference=ok"
            else:
                return False, f"status={resp.status} body={body[:200]}"
    except (HTTPError, URLError, ValueError, TimeoutError, OSError) as e:
        return False, f"error: {e}"


def gather_diagnostics() -> str:
    """Collect system diagnostics for the Claude agent."""
    diag_parts = []

    # Service status
    for cmd, label in [
        (["systemctl", "status", "text-generator-inference.service", "--no-pager", "-l"], "systemd service status"),
        (["journalctl", "-u", "text-generator-inference.service", "--no-pager", "-n", "50"], "recent journal logs"),
        (["tail", "-n", "80", "/var/log/supervisor/text-generator-inference.log"], "inference stdout log"),
        (["tail", "-n", "40", "/var/log/supervisor/text-generator-inference-error.log"], "inference stderr log"),
        (["nvidia-smi"], "GPU status"),
        (["supervisorctl", "status"], "supervisor status (cloudflared tunnels)"),
    ]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            output = (result.stdout + result.stderr).strip()
            diag_parts.append(f"### {label}\n```\n{output[-2000:]}\n```")
        except Exception as e:
            diag_parts.append(f"### {label}\n```\nFailed to collect: {e}\n```")

    return "\n\n".join(diag_parts)


CLAUDE_FIX_PROMPT = """The text-generator.io inference server is DOWN. The liveness check at
{url} failed with: {error_detail}

## Your task
Diagnose why the inference server is not responding, fix it, and verify the fix.

## System diagnostics
{diagnostics}

## Architecture
- Inference server: systemd service `text-generator-inference.service`
  - Port: 9080
  - Command: gunicorn + uvicorn running `questions.inference_server.inference_server:app`
  - Working directory: /nvme0n1-disk/code/text-generator.io
  - Venv: /nvme0n1-disk/code/text-generator.io/.venv
  - Logs: /var/log/supervisor/text-generator-inference.log and -error.log
  - Environment: PRELOAD_MODELS=0, KEEP_ALL_ON_GPU=0, MAX_CACHED_MODELS=3, MIN_FREE_VRAM_GB=4.0

- Cloudflared tunnel (exposes port 9080 to api.text-generator.io):
  - Managed by supervisor: `cloudflared-inference`
  - Tunnel ID: 32d28856-afad-4204-b241-7de8950b2c58
  - Config: /etc/supervisor/conf.d/cloudflared.conf

- Web site service: `text-generator-site.service` on port 8083
  - Tunnel: `cloudflared-site` (supervisor)

## Common failure modes
1. OOM / CUDA out of memory - check nvidia-smi, may need to kill stale GPU processes
2. Python exception on startup - check error log for tracebacks
3. Gunicorn worker timeout - the worker crashed and didn't respawn
4. Cloudflared tunnel down - external URL fails but localhost works
5. Port conflict - something else grabbed port 9080
6. Dependency issue - a package import fails after update

## How to fix
1. Read the logs to identify the root cause
2. If the service is stopped/failed: `sudo systemctl restart text-generator-inference.service`
3. If cloudflared is down: `sudo supervisorctl restart cloudflared-inference`
4. If GPU OOM: check `nvidia-smi`, kill orphan GPU processes if needed, then restart service
5. If a code bug: fix the code, then restart the service
6. After any fix, wait 15-30 seconds for startup, then verify:
   - `curl -s http://localhost:9080/liveness_check` should return {{"inference":"ok"}}
   - `curl -s https://api.text-generator.io/liveness_check` should return {{"inference":"ok"}}
7. If the first fix didn't work, read the NEW logs and try again

IMPORTANT: Always verify the fix worked before finishing. Run the curl checks above.
"""


def spawn_claude_agent(error_detail: str) -> bool:
    """Spawn Codex agent to diagnose and fix. Returns True if fix verified."""
    log("Gathering diagnostics for Codex agent...")
    diagnostics = gather_diagnostics()

    prompt = CLAUDE_FIX_PROMPT.format(
        url=URL_LOCAL,
        error_detail=error_detail,
        diagnostics=diagnostics,
    )

    log(f"Spawning Codex agent (timeout={MAX_AGENT_RUNTIME}s)...")
    try:
        with open(CODEX_LOG_FILE, "a") as codex_log:
            ts = datetime.now(timezone.utc).isoformat()
            codex_log.write(f"\n{'='*80}\n{ts} Agent invocation\n{'='*80}\n")
            codex_log.flush()

            result = subprocess.run(
                [*CODEX_CMD, prompt],
                cwd=str(REPO_ROOT),
                stdout=codex_log,
                stderr=subprocess.STDOUT,
                timeout=MAX_AGENT_RUNTIME,
                text=True,
            )
        log(f"Codex agent exited with code {result.returncode}")
    except subprocess.TimeoutExpired:
        log(f"Codex agent timed out after {MAX_AGENT_RUNTIME}s")
    except FileNotFoundError:
        log(f"ERROR: Codex command not found or not executable: {CODEX_LOCAL}")
        return False
    except Exception as e:
        log(f"ERROR spawning Codex agent: {e}")
        return False

    # Verify fix - wait for service to come up
    log("Waiting 30s for service to stabilize after agent fix...")
    time.sleep(30)

    local_ok, local_detail = check_endpoint(URL_LOCAL)
    if local_ok:
        log(f"FIX VERIFIED - local endpoint OK: {local_detail}")
        external_ok, ext_detail = check_endpoint(URL_EXTERNAL)
        if external_ok:
            log(f"FIX VERIFIED - external endpoint OK: {ext_detail}")
        else:
            log(f"WARNING: local OK but external still failing: {ext_detail}")
        return True
    else:
        log(f"FIX NOT VERIFIED - local still failing: {local_detail}")
        return False


def acquire_lock():
    try:
        lock_fh = open(LOCK_FILE, "w")
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fh
    except BlockingIOError:
        log("Another monitor_inference_agent instance is running; exiting.")
        return None


def main():
    parser = argparse.ArgumentParser(description="Inference server monitor with Claude auto-fix")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL, help="Seconds between checks")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")
    args = parser.parse_args()

    lock_fh = acquire_lock()
    if lock_fh is None:
        return

    log(f"Starting inference monitor (interval={args.interval}s, agent_cooldown={AGENT_COOLDOWN}s)")
    consecutive_failures = 0
    last_agent_time = 0.0
    check_count = 0

    while True:
        check_count += 1
        # Every DEEP_CHECK_EVERY_N cycles, run a real inference check
        use_deep = (check_count % DEEP_CHECK_EVERY_N == 0)
        check_url = URL_LOCAL_DEEP if use_deep else URL_LOCAL
        if use_deep:
            log("Running deep inference check (real model call)...")

        # Check local first
        local_ok, local_detail = check_endpoint(check_url, timeout=120 if use_deep else 30)
        if use_deep and not local_ok:
            log(f"Deep inference check FAILED: {local_detail}")

        if local_ok:
            # Local is good, check external
            external_ok, ext_detail = check_endpoint(URL_EXTERNAL)
            if external_ok:
                log(f"OK - local: {local_detail} | external: {ext_detail}")
            else:
                log(f"LOCAL OK but EXTERNAL DOWN: {ext_detail}")
                # Tunnel issue - try simple restart first
                consecutive_failures += 1
                if consecutive_failures >= FAIL_THRESHOLD:
                    log("Restarting cloudflared-inference tunnel...")
                    subprocess.run(
                        ["sudo", "-n", "supervisorctl", "restart", "cloudflared-inference"],
                        capture_output=True, text=True, timeout=30,
                    )
                    consecutive_failures = 0
            if local_ok:
                consecutive_failures = 0
        else:
            consecutive_failures += 1
            log(f"INFERENCE DOWN ({consecutive_failures}/{FAIL_THRESHOLD}): {local_detail}")

            if consecutive_failures >= FAIL_THRESHOLD:
                now = time.time()
                if now - last_agent_time > AGENT_COOLDOWN:
                    log("Threshold reached - invoking Claude auto-fix agent")
                    fixed = spawn_claude_agent(local_detail)
                    last_agent_time = time.time()
                    if fixed:
                        consecutive_failures = 0
                    else:
                        log("Agent fix did not resolve the issue. Will retry next cycle.")
                        consecutive_failures = 0  # reset to avoid immediate re-trigger
                else:
                    remaining = int(AGENT_COOLDOWN - (now - last_agent_time))
                    log(f"Agent cooldown active ({remaining}s remaining), skipping agent invocation")

        if args.once:
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
