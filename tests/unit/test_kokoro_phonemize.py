import threading
import time

from questions.inference_server import kokoro


def test_phonemize_serializes_shared_espeak_backend(monkeypatch):
    calls_active = 0
    max_active = 0
    state_lock = threading.Lock()

    class FakeBackend:
        def phonemize(self, texts):
            nonlocal calls_active, max_active
            with state_lock:
                calls_active += 1
                max_active = max(max_active, calls_active)
            time.sleep(0.02)
            with state_lock:
                calls_active -= 1
            return ["hello"]

    monkeypatch.setitem(kokoro.phonemizers, "a", FakeBackend())

    threads = [
        threading.Thread(target=kokoro.phonemize, args=(f"hello {idx}", "a"))
        for idx in range(4)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert max_active == 1

