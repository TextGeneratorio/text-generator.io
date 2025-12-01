import json
import logging
import os

import requests

from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

from use_cases_to_generate import use_cases


def make_request(use_case, retries=0):
    use_case["generate_params"].pop("frequencyPenalty", None)
    use_case["generate_params"].pop("repetitionPenalty", None)

    request = requests.post(
        # "http://0.0.0.0:8000/api/v1/generate",
        "https://api.text-generator.io/api/v1/generate",
        data=json.dumps(use_case["generate_params"]),
        headers={"Content-Type": "application/json", "secret": os.getenv("TEXTGENERATOR_API_KEY")},
    )
    if request.status_code == 200:
        return request.json()
    elif retries < 3:
        logger.error(f"Request failed with status code {request.status_code}, retrying...")
        logger.info(f"Request params: {json.dumps(use_case['generate_params'])}")
        logger.info(f"Request response: {request.text}")
        return make_request(use_case, retries + 1)
    else:
        logger.error("Request failed")


existing_use_cases = {}
try:
    with open("questions/usecase_fixtures.py", "r") as f:
        exec(f.read(), {}, existing_use_cases)
    existing_use_cases = existing_use_cases.get("use_cases", {})
except FileNotFoundError:
    pass

for use_case_name, use_case in use_cases.items():
    if use_case_name not in existing_use_cases:
        results = make_request(use_case)
        use_cases[use_case_name]["results"] = results
        logger.info(f"Use case {use_case_name} generated")
    else:
        use_cases[use_case_name]["results"] = existing_use_cases[use_case_name]["results"]
        logger.info(f"Use case {use_case_name} loaded from fixtures")
    logger.info(use_cases)

with open("questions/usecase_fixtures.py", "w") as f:
    f.write(f"use_cases = {repr(use_cases)}")
    logger.info("Use cases written to questions/usecase_fixtures.py")
# openai use cases
# for use_case_name, use_case in openai_examples_map.items():
#     results = make_request(use_case)
#
#     openai_examples_map[use_case_name]["results"] = results
#     logger.info(f"Use case {use_case_name} generated")
#     logger.info(openai_examples_map)
