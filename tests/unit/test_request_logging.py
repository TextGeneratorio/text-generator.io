import os
import sys
import types
from types import SimpleNamespace

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["BCRYPT_PEPPER"] = "pepper"
os.environ["GOOGLE_CLOUD_PROJECT"] = "local"
os.environ["DATASTORE_EMULATOR_HOST"] = "localhost:1234"

sys.modules["sellerinfo"] = types.SimpleNamespace(STRIPE_LIVE_SECRET="", STRIPE_LIVE_KEY="", CLAUDE_API_KEY="")

import main


def test_format_request_url_for_log_leaves_short_urls(monkeypatch):
    monkeypatch.setattr(main, "MAX_REQUEST_LOG_URL_LENGTH", 128)
    request = SimpleNamespace(url="https://text-generator.io/playground?text=short")

    assert main.format_request_url_for_log(request) == "https://text-generator.io/playground?text=short"


def test_format_request_url_for_log_truncates_long_urls(monkeypatch):
    monkeypatch.setattr(main, "MAX_REQUEST_LOG_URL_LENGTH", 80)
    request = SimpleNamespace(url="https://text-generator.io/playground?text=" + ("x" * 200))

    formatted = main.format_request_url_for_log(request)

    assert len(formatted) == 80
    assert formatted.startswith("https://text-generator.io/playground")
    assert "truncated" in formatted
