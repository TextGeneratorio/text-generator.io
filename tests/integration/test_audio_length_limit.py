import os
import pytest

pytestmark = pytest.mark.integration

from starlette.testclient import TestClient

from questions.inference_server.inference_server import app, audio_process

client = TestClient(app)

API_KEY = os.environ.get("TEXT_GENERATOR_API_KEY", "test")
headers = {"secret": API_KEY}


@pytest.mark.skipif(os.getenv("CI") == "true", reason="skip heavy audio test in CI")
def test_audio_word_limit():
    text = "hello"
    prev_len = 0
    max_words = None
    for i in range(1, 30):
        rate, audio = audio_process(text, "af_nicole")
        assert rate == 24000
        cur_len = len(audio)
        if cur_len <= prev_len:
            max_words = len(text.split()) - 1
            break
        prev_len = cur_len
        text += " hello"
    assert max_words is not None
