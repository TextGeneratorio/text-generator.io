import requests
import os

API_KEY = os.getenv("TEXTGENERATOR_API_KEY")
if API_KEY is None:
    raise Exception(
        "Please set TEXTGENERATOR_API_KEY environment variable, login to https://text-generator.io to get your API key")
headers = {"secret": API_KEY}

def generate_summary(text, max_length=1000):
    params = {
        "text": text,
        "max_length": max_length
    }
    response = requests.post(
        "https://api.text-generator.io/api/v1/summarization",
        json=params,
        headers=headers
    )
    return response.json()

# Example usage
long_text = requests.get("https://paste.sh/687a2a81-4e9c-45f8-b3f7-7682b42f5bb5").text

# Generate a brief summary (300 characters)
short_summary = generate_summary(long_text, max_length=15000)
print("Short summary:", short_summary)

# Generate a detailed summary (1000 characters)
# detailed_summary = generate_summary(long_text, max_length=1000)
# print("Detailed summary:", detailed_summary)
