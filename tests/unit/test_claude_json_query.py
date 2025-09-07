import pytest

from questions.inference_server.claude_queries import query_to_claude_json_async

pytestmark = [pytest.mark.inference]


@pytest.mark.asyncio
async def test_query_to_claude_json_async(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        class Resp:
            def raise_for_status(self):
                pass

            async def json(self):
                return {"content": [{"type": "tool_use", "input": {"score": 0.5}}]}

        return Resp()

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        post = fake_post

    monkeypatch.setattr("aiohttp.ClientSession", lambda: FakeSession())
    schema = {"type": "object", "properties": {"score": {"type": "number"}}, "required": ["score"]}
    result = await query_to_claude_json_async("hi", schema)
    assert result == {"score": 0.5}
