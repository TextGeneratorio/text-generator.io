import time
import threading

import pytest

from questions.inference_server.vllm_backend_manager import BackendManager, BackendRegistry


def test_backend_startup_failure_uses_cooldown(monkeypatch):
    launches = []

    class ExitedProcess:
        returncode = 1
        pid = 1234

        def poll(self):
            return self.returncode

    def fake_popen(*args, **kwargs):
        launches.append((args, kwargs))
        return ExitedProcess()

    manager = BackendManager(
        cmd="fake-vllm",
        idle_seconds=0,
        startup_timeout=1,
        failure_cooldown_seconds=30,
    )
    monkeypatch.setattr(manager, "_ready", lambda: False)
    monkeypatch.setattr(manager, "_listening", lambda: False)
    monkeypatch.setattr("questions.inference_server.vllm_backend_manager.subprocess.Popen", fake_popen)

    with pytest.raises(RuntimeError, match="backend exited during startup"):
        manager.ensure_up()

    assert len(launches) == 1

    with pytest.raises(RuntimeError, match="backend startup failed recently"):
        manager.ensure_up()

    assert len(launches) == 1

    manager._last_startup_failure_at = time.time() - 31

    with pytest.raises(RuntimeError, match="backend exited during startup"):
        manager.ensure_up()

    assert len(launches) == 2


def test_maintenance_hold_blocks_starts_until_stop_finishes():
    stop_started = threading.Event()
    release_stop = threading.Event()
    ensure_called = threading.Event()
    ensure_errors = []

    class FakeManager:
        proc = None

        def stop(self):
            stop_started.set()
            release_stop.wait(timeout=1)

        def ensure_up(self):
            ensure_called.set()

    registry = BackendRegistry({"default": FakeManager()}, "default")
    hold_thread = threading.Thread(target=registry.hold, args=(30,))
    hold_thread.start()
    assert stop_started.wait(timeout=0.5)

    def ensure():
        try:
            registry.ensure()
        except RuntimeError as exc:
            ensure_errors.append(str(exc))

    ensure_thread = threading.Thread(target=ensure)
    ensure_thread.start()
    assert not ensure_called.wait(timeout=0.05)

    release_stop.set()
    hold_thread.join(timeout=1)
    ensure_thread.join(timeout=1)

    assert not hold_thread.is_alive()
    assert not ensure_thread.is_alive()
    assert ensure_called.is_set() is False
    assert ensure_errors and "held for maintenance" in ensure_errors[0]
