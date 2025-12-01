import json
import logging
import os

import requests

from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

from questions.usecase_fixtures import use_cases

API_URL = "https://api.text-generator.io/api/v1/generate"


def generate_description(text):
    payload = {
        "text": f"Provide a detailed description for the following use case example: {text}",
        "number_of_results": 1,
        "max_length": 120,
        "temperature": 0.7,
    }
    response = requests.post(
        API_URL,
        headers={"Content-Type": "application/json", "secret": os.getenv("TEXTGENERATOR_API_KEY")},
        data=json.dumps(payload),
    )
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list):
            return data[0].get("generated_text", "")
    logger.error(f"Failed to generate description: {response.status_code} {response.text}")
    return ""


for key, case in use_cases.items():
    description = generate_description(case.get("description", ""))
    case["long_description"] = description
    logger.info(f"Generated long description for {key}")

with open("questions/usecase_fixtures.py", "w") as f:
    f.write(f"use_cases = {repr(use_cases)}")
    logger.info("Updated usecase_fixtures with long descriptions")
