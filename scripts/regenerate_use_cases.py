"""Regenerate all use cases by calling the local inference server."""
import json
import logging
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")
from scripts.use_cases_to_generate import use_cases

SERVER_URL = "http://localhost:9080/api/v1/generate"
SECRET = "DjbkCN1iAYnz4oj28QqOEORl84jKSeUT"


def make_request(use_case, retries=0):
    params = dict(use_case["generate_params"])
    params.pop("frequencyPenalty", None)
    params.pop("repetitionPenalty", None)

    try:
        response = requests.post(
            SERVER_URL,
            json=params,
            headers={"Content-Type": "application/json", "secret": SECRET},
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()
        elif retries < 3:
            logger.warning(f"Status {response.status_code}, retrying ({retries+1}/3)...")
            time.sleep(2)
            return make_request(use_case, retries + 1)
        else:
            logger.error(f"Failed after 3 retries: {response.status_code} {response.text[:200]}")
            return None
    except Exception as e:
        if retries < 3:
            logger.warning(f"Error: {e}, retrying ({retries+1}/3)...")
            time.sleep(2)
            return make_request(use_case, retries + 1)
        logger.error(f"Failed after 3 retries: {e}")
        return None


total = len(use_cases)
success = 0
failed = 0

for i, (name, use_case) in enumerate(use_cases.items(), 1):
    logger.info(f"[{i}/{total}] Generating: {name}")
    results = make_request(use_case)
    if results:
        use_cases[name]["results"] = results
        success += 1
        # Show a preview
        first_result = results[0]["generated_text"][:80] if results else "empty"
        logger.info(f"  OK: {first_result}...")
    else:
        use_cases[name]["results"] = [{"generated_text": "", "stop_reason": "error"}]
        failed += 1
        logger.error(f"  FAILED: {name}")

# Write output
with open("questions/usecase_fixtures.py", "w") as f:
    f.write(f"use_cases = {repr(use_cases)}")

logger.info(f"Done! {success} succeeded, {failed} failed out of {total}")
