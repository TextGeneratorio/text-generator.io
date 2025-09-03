import traceback

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.internet]
import logging

from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

from requests_futures.sessions import FuturesSession

from questions.utils import log_time

session = FuturesSession(max_workers=10)
"""
End to end performance test, you need to do docker-compose up to run this test. see README.md

Not a full replacement for the e2e latency tests
"""
SERVER_URL = "https://text-generator.io"

# makes this many concurrent requests
CONCURRENT_REQUESTS = 4


@pytest.mark.asyncio
async def test_model_performance():
    failed_count = 0
    success_count = 0
    with log_time("performance test"):
        for end_idx in range(100):
            with log_time("one run"):
                requests = [make_request() for _ in range(CONCURRENT_REQUESTS)]
                for request in requests:
                    try:
                        response = request.result()
                        if not str(response.status_code).startswith("2"):
                            text = response.text
                            logger.error(f"server error status code {response.status_code}, body: {text}")
                            failed_count += 1
                        else:
                            success_count += 1

                    except Exception as e:
                        failed_count += 1
                        logger.error(f"request failed: {e} ")
                        # print the stack trace for the failed request
                        logger.error(f"stack trace: {traceback.format_exc()}")
                    else:
                        success_count += 1

            logger.info(f"failed count: {failed_count}")
            logger.info(f"success_count count: {success_count}")


def make_request():
    return session.post(
        SERVER_URL + "/api/v1/generate",
        json={
            "text": "the capital of Papua New Guinea is ",
            "number_of_results": 1,
            "max_length": 100,
            "min_length": 1,
            "max_sentences": 1,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "seed": 0,
        },
    )
