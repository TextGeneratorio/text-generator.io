#!/usr/bin/env python3
"""
Simple Parakeet test
"""
import requests

def test_simple_audio():
    """Test with a simple audio URL"""
    url = "http://localhost:9080/api/v1/audio-extraction"
    
    data = {
        "audio_url": "http://www.fit.vutbr.cz/~motlicek/sympatex/f2bjrop1.0.wav",
        "translate_to_english": False
    }
    
    print(f"Testing: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, json=data, timeout=120)  # 2 minute timeout
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ SUCCESS - Text: {result.get('text', 'No text')}")
        
    except requests.exceptions.Timeout:
        print("⚠️  Timeout - Model is likely loading (this is normal on first run)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_audio()
