import dataclasses
import os
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.internet, pytest.mark.inference]

from fastapi import UploadFile

# set environment var
os.environ["API_KEY"] = "AIzaSyDQX"  # not testing the stripe stuff
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "secrets/google-credentials.json"

from starlette.testclient import TestClient

from questions.inference_server.inference_server import app, audio_process
from questions.post_process_results import post_process_results
from questions.models import GenerateParams, create_generate_params, AudioParams

client = TestClient(app)


def test_audio_extraction_audio_file():
    audio_file = "tests/integ/data/f2bjrop1.0.wav"

    # audio = AudioSegment.from_wav(audio_file)
    audio_params = AudioParams(
        # audio_file=UploadFile(audio_file, open(audio_file, "rb"), "audio/wav"),
        translate_to_english=False,
        output_filetype="txt",
    ).__dict__
    files = {'audio_file': ("audiof.wav", open(audio_file, 'rb'))}
    response = client.post("/api/v1/audio-file-extraction", files=files, data=audio_params)
    assert response.status_code == 200, response.text
    completions = response.json()
    print(completions)


def test_audio_extraction_audio_file_srt():
    audio_file = "tests/integ/data/f2bjrop1.0.wav"

    # audio = AudioSegment.from_wav(audio_file)
    audio_params = AudioParams(
        # audio_file=UploadFile(audio_file, open(audio_file, "rb"), "audio/wav"),
        translate_to_english=False,
        output_filetype="srt",
    ).__dict__
    files = {'audio_file': ("audiof.wav", open(audio_file, 'rb'))}
    response = client.post("/api/v1/audio-file-extraction", files=files, data=audio_params)
    assert response.status_code == 200, response.text
    completions = response.json()
    print(completions)


def test_audio_extraction_txt():
    audio_file = "http://www.fit.vutbr.cz/~motlicek/sympatex/f2bjrop1.0.wav"

    # audio = AudioSegment.from_wav(audio_file)
    audio_params = AudioParams(
        audio_url=audio_file,
        translate_to_english=False,
        output_filetype="txt",
    ).__dict__
    response = client.post("/api/v1/audio-extraction", json=audio_params)
    assert response.status_code == 200, response.text
    completions = response.json()
    print(completions)


def test_audio_extraction_srt():
    audio_file = "tests/integ/data/f2bjrop1.0.wav"
    audio_file = "http://www.fit.vutbr.cz/~motlicek/sympatex/f2bjrop1.0.wav"

    # audio = AudioSegment.from_wav(audio_file)
    audio_params = AudioParams(
        audio_url=audio_file,
        translate_to_english=False,
        output_filetype="srt",
    ).__dict__
    response = client.post("/api/v1/audio-extraction", json=audio_params)
    assert response.status_code == 200, response.text
    completions = response.json()
    print(completions)


def test_audio_extraction_srt_english():
    audio_file = "tests/integ/data/f2bjrop1.0.wav"
    audio_file = "http://www.fit.vutbr.cz/~motlicek/sympatex/f2bjrop1.0.wav"

    # audio = AudioSegment.from_wav(audio_file)
    audio_params = AudioParams(
        audio_url=audio_file,
        translate_to_english=True,
        output_filetype="srt",
    ).__dict__
    response = client.post("/api/v1/audio-extraction", json=audio_params)
    assert response.status_code == 200, response.text
    completions = response.json()
    print(completions)


def test_audio_extraction_mp3():
    audio_file = "tests/integ/data/f2bjrop1.0.wav"
    audio_file = "http://www.fit.vutbr.cz/~motlicek/sympatex/f2bjrop1.0.wav"

    # audio = AudioSegment.from_wav(audio_file)
    audio_params = AudioParams(
        audio_url=audio_file,
        translate_to_english=True,
        output_filetype="srt",
    ).__dict__
    response = client.post("/api/v1/audio-extraction", json=audio_params)
    assert response.status_code == 200, response.text
    completions = response.json()
    print(completions)


def test_audio_extraction_yt_dl():
    audio_file = "https://www.youtube.com/watch?v=uJgzCQYVv44&ab_channel=LeviTheGiant"

    # audio = AudioSegment.from_wav(audio_file)
    audio_params = AudioParams(
        audio_url=audio_file,
        translate_to_english=True,
        output_filetype="srt",
    ).__dict__
    response = client.post("/api/v1/audio-extraction", json=audio_params)
    assert response.status_code == 200, response.text
    completions = response.json()
    print(completions)
