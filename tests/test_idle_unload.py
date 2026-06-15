"""Tests for ModelCache idle unload feature."""

import threading
import time
from unittest.mock import MagicMock

import pytest

from questions.inference_server import model_cache as mc


@pytest.fixture(autouse=True)
def _fast_idle_settings(monkeypatch):
    """Use very short timeouts for testing."""
    monkeypatch.setattr(mc, "IDLE_UNLOAD_SECONDS", 2)
    monkeypatch.setattr(mc, "_IDLE_CHECK_INTERVAL", 0.5)


@pytest.fixture()
def cache():
    return mc.ModelCache()


def test_models_not_loaded_at_init(cache):
    assert len(cache) == 0
    assert cache._last_access_time == 0.0


def test_add_or_get_loads_and_touches(cache):
    result = cache.add_or_get("m1", lambda: "model_1")
    assert result == "model_1"
    assert len(cache) == 1
    assert cache._last_access_time > 0


def test_cache_hit_returns_same_object(cache):
    cache.add_or_get("m1", lambda: "model_1")
    result = cache.add_or_get("m1", lambda: "should_not_be_called")
    assert result == "model_1"


def test_idle_callback_fired_on_unload(cache):
    called = threading.Event()
    cache.register_idle_callback(lambda: called.set())

    cache.add_or_get("m1", lambda: "model_1")

    # Manually trigger idle unload
    with cache._idle_lock:
        cache._unload_all_idle()

    assert len(cache) == 0
    assert called.is_set()


def test_idle_unload_clears_most_recent_name(cache):
    cache.add_or_get("m1", lambda: "model_1")
    assert cache.most_recent_name == "m1"

    with cache._idle_lock:
        cache._unload_all_idle()

    assert cache.most_recent_name is None


def test_model_reloads_after_idle_unload(cache):
    cache.add_or_get("m1", lambda: "v1")

    with cache._idle_lock:
        cache._unload_all_idle()
    assert len(cache) == 0

    result = cache.add_or_get("m1", lambda: "v2")
    assert result == "v2"
    assert len(cache) == 1


def test_timed_idle_unload(cache):
    """Models auto-unload after IDLE_UNLOAD_SECONDS of no access."""
    unloaded = threading.Event()
    cache.register_idle_callback(lambda: unloaded.set())

    cache.add_or_get("m1", lambda: "model_1")
    assert cache._idle_thread is not None

    # Should still be loaded after 1s (threshold is 2s)
    time.sleep(1)
    assert len(cache) == 1

    # Wait for unload (2s idle + up to 0.5s check interval + margin)
    assert unloaded.wait(timeout=5), "Idle unload did not fire within timeout"
    assert len(cache) == 0


def test_access_resets_idle_timer(cache):
    """Accessing a model resets the idle countdown."""
    cache.add_or_get("m1", lambda: "model_1")

    # Keep touching every 1s — should prevent unload at the 2s threshold
    for _ in range(4):
        time.sleep(1)
        cache.add_or_get("m1", lambda: "should_not_load")
        assert len(cache) == 1, "Model was unloaded despite recent access"


def test_idle_thread_stops_when_cache_empty(cache):
    """The idle checker thread should exit when cache is already empty."""
    cache.add_or_get("m1", lambda: "model_1")

    with cache._idle_lock:
        cache._unload_all_idle()

    # Give the checker thread time to notice and exit
    time.sleep(1.5)
    assert cache._idle_thread is None or not cache._idle_thread.is_alive()


def test_multiple_models_all_unloaded(monkeypatch):
    """All models get unloaded when idle, not just LRU."""
    monkeypatch.setattr(mc, "MAX_CACHED_MODELS", 5)
    cache = mc.ModelCache()

    cache.add_or_get("m1", lambda: "model_1")
    cache.add_or_get("m2", lambda: "model_2")
    cache.add_or_get("m3", lambda: "model_3")
    assert len(cache) == 3

    with cache._idle_lock:
        cache._unload_all_idle()

    assert len(cache) == 0


def test_to_cpu_called_on_unload(cache):
    """Models with .to() method get moved to CPU before deletion."""
    mock_model = MagicMock()
    cache.add_or_get("m1", lambda: mock_model)

    with cache._idle_lock:
        cache._unload_all_idle()

    mock_model.to.assert_called_once_with("cpu")


def test_tuple_models_all_moved_to_cpu(cache):
    """Tuple of models (e.g. model+voicepacks) all get .to('cpu')."""
    m1 = MagicMock()
    m2 = MagicMock()
    cache.add_or_get("m1", lambda: (m1, m2))

    with cache._idle_lock:
        cache._unload_all_idle()

    m1.to.assert_called_once_with("cpu")
    m2.to.assert_called_once_with("cpu")


def test_disabled_when_zero(monkeypatch):
    """No idle thread is started when IDLE_UNLOAD_SECONDS=0."""
    monkeypatch.setattr(mc, "IDLE_UNLOAD_SECONDS", 0)
    cache = mc.ModelCache()

    cache.add_or_get("m1", lambda: "model_1")
    assert cache._idle_thread is None
