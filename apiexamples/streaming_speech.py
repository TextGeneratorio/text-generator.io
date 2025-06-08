import requests
import os

API_KEY = os.getenv("TEXT_GENERATOR_API_KEY")
if API_KEY is None:
    raise Exception(
        "Please set TEXT_GENERATOR_API_KEY environment variable, login to https://text-generator.io to get your API key")
headers = {"secret": API_KEY}

params = {
    "text": "Hello streaming world",
    "speaker": "Male fast"
}
with requests.post("https://api.text-generator.io/api/v1/generate_speech_stream", json=params, headers=headers, stream=True) as r:
    for chunk in r.iter_content(chunk_size=None):
        print("Received", len(chunk), "bytes")
