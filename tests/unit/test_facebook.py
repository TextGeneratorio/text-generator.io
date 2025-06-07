import base64
import hashlib
import hmac
import json

import sys
import urllib.request as urllib_request
import http.client as http_client
import urllib.parse as urllib_parse
import cgi

sys.modules.setdefault("urllib2", urllib_request)
sys.modules.setdefault("httplib", http_client)
sys.modules.setdefault("urlparse", urllib_parse)
cgi.parse_qs = urllib_parse.parse_qs

from gameon.facebook import parse_signed_request  # noqa: E402


def make_signed_request(data: dict, secret: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    sig = hmac.new(secret.encode('ascii'), msg=payload.encode('ascii'), digestmod=hashlib.sha256).digest()
    encoded_sig = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{encoded_sig}.{payload}"


def test_parse_signed_request_valid():
    secret = "secret"
    data = {"algorithm": "HMAC-SHA256", "user_id": "123"}
    sr = make_signed_request(data, secret)
    result = parse_signed_request(sr, secret)
    assert result == data


def test_parse_signed_request_invalid_signature():
    secret = "secret"
    data = {"algorithm": "HMAC-SHA256", "user_id": "123"}
    sr = make_signed_request(data, secret)
    assert parse_signed_request(sr, "wrong") is False
