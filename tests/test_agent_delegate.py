"""Tests for the subagent delegation system."""

import json
from unittest.mock import AsyncMock

import pytest

from questions.agent.delegate import BLOCKED_TOOLS, MAX_DEPTH, run_subagent
from questions.agent.registry import ToolRegistry, registry


@pytest.fixture(autouse=True)
def clean_registry():
    ToolRegistry.reset()
    yield
    ToolRegistry.reset()


def _mock_response(content="Done!", tool_calls=None, finish_reason="stop"):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
        finish_reason = "tool_calls"
    return {
        "choices": [{"message": message, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
    }


class TestSubagentExecution:
    @pytest.mark.asyncio
    async def test_simple_subagent(self):
        chat_fn = AsyncMock(return_value=_mock_response("Task completed"))

        result = await run_subagent(
            goal="Write a poem",
            context="About cats",
            chat_fn=chat_fn,
        )

        assert result["status"] == "completed"
        assert result["result"] == "Task completed"
        assert result["iterations_used"] == 1
        assert result["tool_calls_made"] == []

    @pytest.mark.asyncio
    async def test_subagent_with_tool_calls(self):
        registry.register(
            name="calculator",
            toolset="utility",
            schema={
                "name": "calculator",
                "description": "Calc",
                "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}},
            },
            handler=lambda args, **kw: json.dumps({"result": 42}),
        )

        call_count = 0

        async def mock_chat(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_response(
                    content=None,
                    tool_calls=[
                        {
                            "id": "tc_1",
                            "function": {"name": "calculator", "arguments": '{"expression": "6*7"}'},
                        }
                    ],
                )
            return _mock_response("The answer is 42")

        result = await run_subagent(
            goal="Calculate 6*7",
            context=None,
            chat_fn=mock_chat,
            tools_enabled=["calculator"],
        )

        assert result["status"] == "completed"
        assert len(result["tool_calls_made"]) == 1
        assert result["tool_calls_made"][0]["name"] == "calculator"
        assert result["iterations_used"] == 2

    @pytest.mark.asyncio
    async def test_subagent_blocked_tools(self):
        # Register a blocked tool
        registry.register(
            name="delegate_task",
            toolset="delegation",
            schema={
                "name": "delegate_task",
                "description": "Delegate",
                "parameters": {"type": "object", "properties": {}},
            },
            handler=lambda args, **kw: json.dumps({"ok": True}),
        )

        call_count = 0

        async def mock_chat(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_response(
                    content=None,
                    tool_calls=[
                        {
                            "id": "tc_1",
                            "function": {"name": "delegate_task", "arguments": "{}"},
                        }
                    ],
                )
            return _mock_response("Can't delegate from subagent")

        result = await run_subagent(goal="Delegate something", context=None, chat_fn=mock_chat)

        # Tool call should have been blocked
        assert len(result["tool_calls_made"]) == 1
        assert "not available" in result["tool_calls_made"][0]["result"]

    @pytest.mark.asyncio
    async def test_subagent_max_depth(self):
        chat_fn = AsyncMock()

        result = await run_subagent(
            goal="Too deep",
            context=None,
            chat_fn=chat_fn,
            depth=MAX_DEPTH,
        )

        assert result["status"] == "error"
        assert "depth exceeded" in result["result"]
        chat_fn.assert_not_called()

    @pytest.mark.asyncio
    async def test_subagent_max_iterations(self):
        registry.register(
            name="noop",
            toolset="test",
            schema={"name": "noop", "description": "No-op", "parameters": {"type": "object", "properties": {}}},
            handler=lambda args, **kw: json.dumps({"ok": True}),
        )

        async def always_call_tool(messages, **kwargs):
            return _mock_response(
                content=None,
                tool_calls=[
                    {"id": "tc", "function": {"name": "noop", "arguments": "{}"}}
                ],
            )

        result = await run_subagent(
            goal="Loop",
            context=None,
            chat_fn=always_call_tool,
            max_iterations=3,
        )

        assert result["iterations_used"] == 3

    @pytest.mark.asyncio
    async def test_subagent_api_error(self):
        async def fail(**kwargs):
            raise RuntimeError("Connection refused")

        result = await run_subagent(
            goal="Will fail",
            context=None,
            chat_fn=fail,
        )

        assert result["status"] == "error"
        assert "Connection refused" in result["result"]


class TestBlockedTools:
    def test_blocked_tools_list(self):
        assert "delegate_task" in BLOCKED_TOOLS
        assert "cron_create" in BLOCKED_TOOLS
        assert "cron_delete" in BLOCKED_TOOLS
        assert "skill_create" in BLOCKED_TOOLS
        assert "skill_delete" in BLOCKED_TOOLS
