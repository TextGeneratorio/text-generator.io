#!/usr/bin/env python3
"""
Test Parakeet ASR with file upload
"""
import requests
import numpy as np
import tempfile
import os
from scipy.io.wavfile import write

def create_test_audio():
    """Create a simple test audio file"""
    # Create a simple sine wave audio file
    sample_rate = 16000
    duration = 1  # seconds
    frequency = 440  # A4 note
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(frequency * 2 * np.pi * t)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Convert to 16-bit integers
        audio_int = (audio * 32767).astype(np.int16)
        write(f.name, sample_rate, audio_int)
        return f.name

def test_parakeet_file_upload():
    """Test Parakeet ASR with file upload"""
    print("=== Testing Parakeet ASR File Upload ===")
    
    # Create test audio file
    audio_file = create_test_audio()
    print(f"Created test audio file: {audio_file}")
    
    try:
        # Test file upload endpoint
        url = "http://localhost:9080/api/v1/audio-file-extraction"
        
        with open(audio_file, 'rb') as f:
            files = {'file': ('test.wav', f, 'audio/wav')}
            data = {'translate_to_english': 'false'}
            
            print(f"Uploading to: {url}")
            response = requests.post(url, files=files, data=data, timeout=30)
            
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Parakeet ASR is working")
            print(f"Transcription result: {result}")
            return True
        else:
            print(f"❌ FAIL - Status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(audio_file):
            os.unlink(audio_file)

if __name__ == "__main__":
    # Install scipy if needed
    try:
        import scipy.io.wavfile
    except ImportError:
        print("Installing scipy...")
        os.system("pip install scipy")
        import scipy.io.wavfile
    
    success = test_parakeet_file_upload()
    if success:
        print("\n🎉 Parakeet ASR is working correctly!")
    else:
        print("\n⚠️  Parakeet ASR test failed")
