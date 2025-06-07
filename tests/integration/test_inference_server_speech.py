import os
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.internet]

from questions.utils import log_time

# set environment var
os.environ["API_KEY"] = "AIzaSyDQX"  # not testing the stripe stuff
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "secrets/google-credentials.json"

from starlette.testclient import TestClient

from questions.inference_server.inference_server import app, audio_process
from questions.models import GenerateSpeechParams

client = TestClient(app)

API_KEY = os.environ.get("TEXT_GENERATOR_API_KEY")
headers = {"secret": API_KEY}


def test_speech_creation():
    with log_time("speech creation"):
        result = audio_process(
            "It is not in the stars to hold our destiny but in ourselves." * 10,
            "Male fast",
        )
        assert result is not None
        assert result[0] is not None


def test_generate_speech_route_single_voice():
    audio_params = GenerateSpeechParams(
        text="Text-Generator.io is bringing the cost of intelligence toward zero.",
        speaker="Male fast",
    )
    response = client.post(
        "/api/v1/generate_speech", json=audio_params.__dict__, headers=headers
    )
    assert response.status_code == 200, response.text
    binary_file_response = response.content
    assert binary_file_response is not None
    with open("test.wav", "wb") as f:
        f.write(binary_file_response)


speakers = [
    "Male fast",
    "Female 1",
    "Male default",
    "Male slower",
    "Female 2",
]


def test_generate_speech_route_all_voices():
    for speaker in speakers:
        audio_params = GenerateSpeechParams(
            text="Text-Generator.io is bringing the cost of intelligence toward zero.",
            speaker=speaker,
        )
        response = client.post(
            "/api/v1/generate_speech", json=audio_params.__dict__, headers=headers
        )
        assert response.status_code == 200, response.text
        binary_file_response = response.content
        assert binary_file_response is not None
        with open(f"static/audio/test-{speaker.replace(' ', '-')}.wav", "wb") as f:
            f.write(binary_file_response)
