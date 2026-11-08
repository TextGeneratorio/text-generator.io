import pytest
from fastapi.testclient import TestClient

import main


@pytest.mark.parametrize(
    "path",
    ["/", "/blog/over-10x-openai-cost-savings-one-line-change"],
)
def test_pages_do_not_load_broken_affiliate_tracker(path):
    client = TestClient(main.app, raise_server_exceptions=False)

    response = client.get(path)

    assert response.status_code == 200
    assert "evangeler-tracking.js" not in response.text
    assert "window.evangelTrackingCode" not in response.text
    assert "frontend-error-logger.js" in response.text
