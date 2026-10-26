import json
import threading
import time

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
        coexisting_unload_url="",
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


def test_cold_start_clears_coexisting_vram_before_launch(monkeypatch):
    events = []

    class RunningProcess:
        returncode = None
        pid = 1234

        def poll(self):
            return self.returncode

    manager = BackendManager(
        cmd="fake-vllm",
        idle_seconds=0,
        startup_timeout=1,
        failure_cooldown_seconds=0,
    )
    ready = iter([False, False, True])
    monkeypatch.setattr(manager, "_ready", lambda: next(ready, True))
    monkeypatch.setattr(manager, "_listening", lambda: False)
    monkeypatch.setattr(manager, "_clear_coexisting_vram", lambda: events.append("clear") or True)
    monkeypatch.setattr(
        "questions.inference_server.vllm_backend_manager.subprocess.Popen",
        lambda *args, **kwargs: events.append("launch") or RunningProcess(),
    )

    manager.ensure_up()

    assert events == ["clear", "launch"]


def test_busy_coexisting_model_prevents_unsafe_launch(monkeypatch):
    manager = BackendManager(
        cmd="fake-vllm",
        idle_seconds=0,
        startup_timeout=1,
        failure_cooldown_seconds=0,
    )
    monkeypatch.setattr(manager, "_ready", lambda: False)
    monkeypatch.setattr(manager, "_listening", lambda: False)
    monkeypatch.setattr(manager, "_clear_coexisting_vram", lambda: False)
    monkeypatch.setattr(
        "questions.inference_server.vllm_backend_manager.subprocess.Popen",
        lambda *args, **kwargs: pytest.fail("backend must not launch without VRAM headroom"),
    )

    with pytest.raises(RuntimeError, match="did not release VRAM"):
        manager.ensure_up()

    status = manager.status()
    assert "did not release VRAM" in status["last_startup_failure"]


def test_coexisting_clear_retries_until_loaded_list_is_empty(monkeypatch):
    replies = iter([
        {"loaded": ["zimage"]},
        {"loaded": ["zimage"]},
        {"loaded": []},
    ])
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(next(replies)).encode()

    manager = BackendManager(
        cmd="fake-vllm",
        idle_seconds=0,
        coexisting_clear_timeout=1,
        coexisting_clear_poll=0.05,
    )
    monkeypatch.setattr(
        "questions.inference_server.vllm_backend_manager.urllib.request.urlopen",
        lambda *args, **kwargs: calls.append((args, kwargs)) or FakeResponse(),
    )
    monkeypatch.setattr(
        "questions.inference_server.vllm_backend_manager.time.sleep",
        lambda _seconds: None,
    )

    assert manager._clear_coexisting_vram() is True
    assert len(calls) == 3


def test_coexisting_hold_spans_cold_start(monkeypatch):
    events = []

    class RunningProcess:
        returncode = None
        pid = 1234

        def poll(self):
            return None

    manager = BackendManager(
        cmd="fake-vllm",
        idle_seconds=0,
        startup_timeout=1,
        failure_cooldown_seconds=0,
    )
    ready = iter([False, False, True])
    monkeypatch.setattr(manager, "_ready", lambda: next(ready, True))
    monkeypatch.setattr(manager, "_listening", lambda: False)
    monkeypatch.setattr(manager, "_hold_coexisting_vram", lambda: events.append("hold") or True)
    monkeypatch.setattr(manager, "_clear_coexisting_vram", lambda: events.append("clear") or True)
    monkeypatch.setattr(manager, "_release_coexisting_vram", lambda: events.append("release"))
    monkeypatch.setattr(
        "questions.inference_server.vllm_backend_manager.subprocess.Popen",
        lambda *args, **kwargs: events.append("launch") or RunningProcess(),
    )

    manager.ensure_up()

    assert events == ["hold", "clear", "launch", "release"]


def test_busy_image_during_wake_keeps_sleeping_backend_for_retry(monkeypatch):
    class SleepingProcess:
        pid = 4321

        def poll(self):
            return None

    manager = BackendManager(
        cmd="fake-vllm",
        idle_seconds=0,
        failure_cooldown_seconds=30,
    )
    manager.proc = SleepingProcess()
    manager.sleeping = True
    monkeypatch.setattr(manager, "_hold_coexisting_vram", lambda: True)
    monkeypatch.setattr(manager, "_clear_coexisting_vram", lambda: False)
    monkeypatch.setattr(manager, "_release_coexisting_vram", lambda: None)
    monkeypatch.setattr(
        manager,
        "_stop_locked",
        lambda: pytest.fail("a busy image must not destroy the sleeping vLLM process"),
    )

    with pytest.raises(RuntimeError, match="before backend wake"):
        manager.ensure_up()
    assert manager.proc is not None
    assert manager.sleeping is True

    with pytest.raises(RuntimeError, match="startup failed recently"):
        manager.ensure_up()


def test_status_exposes_startup_failure_and_retry_delay(monkeypatch):
    manager = BackendManager(
        cmd="fake-vllm",
        idle_seconds=0,
        failure_cooldown_seconds=30,
        coexisting_unload_url="",
    )
    manager._record_startup_failure("backend exited during startup (code 1)")
    monkeypatch.setattr(manager, "_ready", lambda: False)

    status = manager.status()

    assert status["starting"] is False
    assert status["last_startup_failure"] == "backend exited during startup (code 1)"
    assert 0 < status["startup_retry_after_seconds"] <= 30


def test_registry_request_pins_backend_and_blocks_sleep(monkeypatch):
    class RunningProcess:
        pid = 9876

        def poll(self):
            return None

    manager = BackendManager(
        cmd="fake-vllm",
        idle_seconds=0,
        coexisting_unload_url="",
    )
    manager.proc = RunningProcess()
    monkeypatch.setattr(manager, "ensure_up", lambda: None)
    monkeypatch.setattr(
        manager,
        "_post_ctl",
        lambda *_args, **_kwargs: pytest.fail("active inference must not be slept"),
    )
    registry = BackendRegistry({"default": manager}, "default")

    with registry.request() as served:
        assert served == "default"
        assert manager.active_requests() == 1
        assert manager.status()["active_requests"] == 1
        assert registry.sleep_all() is False

    assert manager.active_requests() == 0
