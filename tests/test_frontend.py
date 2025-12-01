from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Text Generator" in response.text
