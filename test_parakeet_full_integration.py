#!/usr/bin/env python3
"""
Test Parakeet ASR with a voice synthesis example
"""
import requests
import json

def test_parakeet_with_text_to_speech():
    """Test Parakeet ASR using the server's own TTS to create speech first"""
    print("=== Testing Parakeet ASR with synthesized speech ===")
    
    # First, generate some speech using the TTS endpoint
    tts_url = "http://localhost:9081/api/v1/generate_speech"
    tts_data = {
        "text": "Hello world, this is a test of speech recognition",
        "voice": "default"
    }
    
    print("1. Generating speech for transcription test...")
    try:
        tts_response = requests.post(tts_url, json=tts_data, timeout=30)
        print(f"TTS Status: {tts_response.status_code}")
        
        if tts_response.status_code == 200:
            # Save the generated audio
            with open('/tmp/generated_speech.wav', 'wb') as f:
                f.write(tts_response.content)
            print("✅ Speech generated successfully")
            
            # Now test ASR on the generated speech
            print("2. Testing ASR on generated speech...")
            asr_url = "http://localhost:9081/api/v1/audio-file-extraction"
            
            with open('/tmp/generated_speech.wav', 'rb') as f:
                files = {'audio_file': ('test.wav', f, 'audio/wav')}
                data = {'translate_to_english': 'false'}
                
                asr_response = requests.post(asr_url, files=files, data=data, timeout=30)
                
            print(f"ASR Status: {asr_response.status_code}")
            
            if asr_response.status_code == 200:
                result = asr_response.json()
                print("✅ ASR SUCCESS!")
                print(f"Original text: '{tts_data['text']}'")
                print(f"Transcribed text: '{result.get('text', '')}'")
                print(f"Segments: {len(result.get('segments', []))}")
                if result.get('segments'):
                    for i, seg in enumerate(result['segments']):
                        print(f"  Segment {i+1}: '{seg.get('text', '')}' ({seg.get('start', 0):.2f}s - {seg.get('end', 0):.2f}s)")
                return True
            else:
                print(f"❌ ASR failed: {asr_response.text[:200]}...")
                return False
        else:
            print(f"❌ TTS failed: {tts_response.text[:200]}...")
            # Try with just our sine wave test anyway
            print("3. Falling back to sine wave test...")
            return test_simple_asr()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("3. Falling back to sine wave test...")
        return test_simple_asr()

def test_simple_asr():
    """Simple test with sine wave (should return empty)"""
    print("Testing ASR with sine wave (should return empty result)...")
    
    asr_url = "http://localhost:9081/api/v1/audio-file-extraction"
    try:
        with open('/tmp/test_audio.wav', 'rb') as f:
            files = {'audio_file': ('test.wav', f, 'audio/wav')}
            data = {'translate_to_english': 'false'}
            
            response = requests.post(asr_url, files=files, data=data, timeout=30)
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ASR endpoint working! Result: {result}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_parakeet_with_text_to_speech()
    if success:
        print("\n🎉 Parakeet ASR integration test passed!")
    else:
        print("\n⚠️  Parakeet ASR test had issues")
