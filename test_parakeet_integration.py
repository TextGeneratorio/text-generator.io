#!/usr/bin/env python3
"""
Integration test for the Parakeet speech-to-text model
"""

import tempfile

import numpy as np
import requests
import soundfile as sf


def create_test_audio():
    """Create a simple test audio file"""
    # Generate a simple sine wave (440 Hz for 2 seconds)
    sample_rate = 16000
    duration = 2.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)

    # Create temporary wav file
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(temp_file.name, audio_data, sample_rate)

    return temp_file.name


def test_audio_extraction_url():
    """Test audio extraction with URL"""
    url = "http://0.0.0.0:8083/api/v1/audio-extraction"

    # Use a sample audio URL (this is from the documentation)
    data = {"audio_url": "http://www.fit.vutbr.cz/~motlicek/sympatex/f2bjrop1.0.wav", "translate_to_english": False}

    try:
        print(f"Testing audio extraction endpoint: {url}")
        response = requests.post(url, json=data, timeout=60)
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Success! Transcribed text: {result.get('text', 'No text found')}")
            if "segments" in result:
                print(f"Number of segments: {len(result['segments'])}")
                for i, segment in enumerate(result["segments"][:3]):  # Show first 3 segments
                    print(
                        f"  Segment {i}: {segment.get('text', '')} ({segment.get('start', 0):.2f}s-{segment.get('end', 0):.2f}s)"
                    )
            return True
        else:
            print(f"Error response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("Request timed out - model might be loading")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_audio_file_extraction():
    """Test audio file extraction with uploaded file"""
    url = "http://0.0.0.0:8083/api/v1/audio-file-extraction"

    try:
        # Create a test audio file
        test_file_path = create_test_audio()
        print(f"Created test audio file: {test_file_path}")

        with open(test_file_path, "rb") as audio_file:
            files = {"audio_file": audio_file}
            data = {"translate_to_english": "false"}

            print(f"Testing audio file extraction endpoint: {url}")
            response = requests.post(url, files=files, data=data, timeout=60)
            print(f"Status code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"Success! Transcribed text: {result.get('text', 'No text found')}")
                return True
            else:
                print(f"Error response: {response.text}")
                return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_inference_server_availability():
    """Test if the inference server endpoints are available"""
    # Check if there's a separate inference server running
    inference_urls = [
        "http://localhost:9080/api/v1/audio-extraction",
        "http://0.0.0.0:9080/api/v1/audio-extraction",
    ]

    for url in inference_urls:
        try:
            # Use a simple test request
            data = {
                "audio_url": "http://www.fit.vutbr.cz/~motlicek/sympatex/f2bjrop1.0.wav",
                "translate_to_english": False,
            }
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                print(f"✓ Inference server found at: {url}")
                result = response.json()
                print(f"  Transcribed text: {result.get('text', 'No text found')}")
                return True
            else:
                print(f"  Status {response.status_code} at {url}: {response.text[:100]}")
        except requests.exceptions.ConnectionError:
            print(f"  No server at {url}")
        except Exception as e:
            print(f"  Error testing {url}: {e}")

    return False


def main():
    print("=== Parakeet Speech-to-Text Integration Test ===\n")

    print("1. Testing main server audio extraction...")
    main_server_works = test_audio_extraction_url()

    print("\n2. Testing main server file upload...")
    file_upload_works = test_audio_file_extraction()

    print("\n3. Testing inference server availability...")
    inference_server_works = test_inference_server_availability()

    print("\n=== Test Summary ===")
    print(f"Main server URL extraction: {'✓ PASS' if main_server_works else '✗ FAIL'}")
    print(f"Main server file upload: {'✓ PASS' if file_upload_works else '✗ FAIL'}")
    print(f"Inference server: {'✓ AVAILABLE' if inference_server_works else '✗ NOT RUNNING'}")

    if main_server_works or file_upload_works or inference_server_works:
        print("\n🎉 Parakeet model is working!")
    else:
        print("\n⚠️  No working speech-to-text endpoints found")
        print("   This might be because:")
        print("   - The Parakeet model isn't loaded yet")
        print("   - NeMo dependencies aren't installed")
        print("   - The inference server isn't running")


if __name__ == "__main__":
    main()
