from types import SimpleNamespace

import pytest

from questions import tool_ai


def test_query_tool_json_routes_to_deepseek_and_parses_fenced_json(monkeypatch):
    captured = {}

    class Router:
        def chat_completion(self, payload):
            captured.update(payload)
            return SimpleNamespace(
                data={"choices": [{"message": {"content": '```json\n{"value":"ready"}\n```'}}]},
                selected_model="or/deepseek-chat",
                provider="openrouter",
            )

    monkeypatch.setattr(tool_ai, "get_provider_router", lambda: Router())
    result = tool_ai.query_tool_json(
        "Return a value",
        {"type": "object", "properties": {"value": {"type": "string"}}},
        system_message="Be concise.",
    )

    assert captured["model"] == "deepseek-v4-flash"
    assert captured["response_format"] == {"type": "json_object"}
    assert result.data == {"value": "ready"}
    assert result.provider == "openrouter"


def test_query_tool_json_rejects_non_json(monkeypatch):
    class Router:
        def chat_completion(self, payload):
            return SimpleNamespace(
                data={"choices": [{"message": {"content": "not json"}}]},
                selected_model="deepseek-chat",
                provider="deepseek",
            )

    monkeypatch.setattr(tool_ai, "get_provider_router", lambda: Router())
    with pytest.raises(tool_ai.ToolAIError):
        tool_ai.query_tool_json("Return a value", {"type": "object"}, system_message="Be concise.")
