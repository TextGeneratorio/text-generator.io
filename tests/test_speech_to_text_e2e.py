"""E2E tests for speech-to-text page.

For JS behavior tests (API key autofill), visit /speech-to-text?test=true in browser.
"""
import pytest
from fastapi.testclient import TestClient
import main


@pytest.fixture
def client():
    return TestClient(main.app)


def test_speech_to_text_page_loads(client):
    """Test that the speech-to-text page loads successfully."""
    response = client.get("/speech-to-text")
    assert response.status_code == 200
    assert "Speech To Text" in response.text


def test_speech_to_text_contains_code_examples(client):
    """Test that code examples are present in the page."""
    response = client.get("/speech-to-text")
    assert response.status_code == 200
    assert "YOUR_API_KEY" in response.text
    assert "audio-extraction" in response.text


def test_speech_to_text_has_jasmine_tests(client):
    """Test that Jasmine test suite is available via ?test=true."""
    response = client.get("/speech-to-text")
    assert response.status_code == 200
    assert "runSpeechToTextTests" in response.text


def test_current_user_401_when_not_authenticated(client):
    """Test that /api/current-user returns 401 when not authenticated."""
    response = client.get("/api/current-user")
    assert response.status_code == 401


def test_speech_to_text_contains_transcribe_buttons(client):
    """Test that transcribe buttons are present."""
    response = client.get("/speech-to-text")
    assert response.status_code == 200
    assert "Transcribe URL" in response.text
    assert "Transcribe File" in response.text


def test_speech_to_text_contains_record_functionality(client):
    """Test that audio recording UI elements are present."""
    response = client.get("/speech-to-text")
    assert response.status_code == 200
    assert "Record Audio" in response.text


def test_speech_to_text_python_example(client):
    """Test that Python code example is present."""
    response = client.get("/speech-to-text")
    assert response.status_code == 200
    assert "import requests" in response.text


def test_speech_to_text_translate_option(client):
    """Test that translate to English option exists."""
    response = client.get("/speech-to-text")
    assert response.status_code == 200
    assert "Translate to English" in response.text
