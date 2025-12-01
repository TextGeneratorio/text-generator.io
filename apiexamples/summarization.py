import os

import requests

API_KEY = os.getenv("TEXT_GENERATOR_API_KEY")
if API_KEY is None:
    raise Exception(
        "Please set TEXT_GENERATOR_API_KEY environment variable, login to https://text-generator.io to get your API key"
    )
headers = {"secret": API_KEY}


def generate_summary(text, max_length=1000):
    params = {"text": text, "max_length": max_length}
    response = requests.post("https://api.text-generator.io/api/v1/summarization", json=params, headers=headers)
    return response.json()["summary"]


# Example usage
long_text = """
Climate change is one of the most pressing challenges facing our world today.
It affects everything from weather patterns to agriculture, from sea levels to biodiversity.
Scientists have observed numerous indicators of climate change, including rising global temperatures,
melting ice caps, and increasing frequency of extreme weather events. These changes have far-reaching
implications for human society, ecosystems, and the planet's future...
"""

# Generate a brief summary (300 characters)
short_summary = generate_summary(long_text, max_length=300)
print("Short summary:", short_summary)

# Generate a detailed summary (1000 characters)
detailed_summary = generate_summary(long_text, max_length=1000)
print("Detailed summary:", detailed_summary)
