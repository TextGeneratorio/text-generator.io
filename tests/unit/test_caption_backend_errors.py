"""Client-vs-backend classification for the image caption proxy.

A caller that uploads bytes PIL cannot decode must receive a 4xx. The
scheduler used to raise on those bytes before validation, which surfaced as
a 500 and then as a retried 503 at the public CuteDSL endpoint.
"""

import pytest
from fastapi import HTTPException

from questions.inference_server import inference_server


class _Response:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


@pytest.mark.parametrize(
    "status, detail",
    [
        (400, "no input supplied"),
        (422, "image is 90000x90000; the cap is 4096 pixels"),
    ],
)
def test_backend_4xx_becomes_caller_400(status, detail):
    with pytest.raises(HTTPException) as exc_info:
        inference_server._raise_for_backend_client_error(
            _Response(status, {"detail": detail})
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == detail


@pytest.mark.parametrize(
    "detail",
    [
        "UnidentifiedImageError: cannot identify image file <_io.BytesIO object>",
        "image could not be decoded: cannot identify image file",
        "ValueError: image did not contain a valid image",
    ],
)
def test_undecodable_image_5xx_becomes_caller_400(detail):
    with pytest.raises(HTTPException) as exc_info:
        inference_server._raise_for_backend_client_error(
            _Response(500, {"detail": detail})
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "image could not be decoded"


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_genuine_backend_failures_are_left_to_raise_for_status(status):
    """Only decode-shaped 5xx are reclassified; real outages stay backend faults."""
    inference_server._raise_for_backend_client_error(
        _Response(status, {"detail": "CUDA out of memory"})
    )


def test_malformed_json_body_is_not_treated_as_client_error():
    inference_server._raise_for_backend_client_error(
        _Response(502, ValueError("no json"))
    )
