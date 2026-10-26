"""Tests for the tool registry system."""

import json

import pytest

from questions.agent.registry import ToolRegistry, registry


@pytest.fixture(autouse=True)
def clean_registry():
    """Reset registry between tests."""
    ToolRegistry.reset()
    yield
    ToolRegistry.reset()


def _dummy_handler(args, **kwargs):
    return json.dumps({"echo": args})


def _make_schema(name, desc="test tool"):
    return {
        "name": name,
        "description": desc,
        "parameters": {
            "type": "object",
            "properties": {"input": {"type": "string"}},
            "required": ["input"],
        },
    }


class TestToolRegistration:
    def test_register_and_get(self):
        registry.register(
            name="test_tool",
            toolset="test",
            schema=_make_schema("test_tool"),
            handler=_dummy_handler,
            description="A test tool",
        )
        entry = registry.get("test_tool")
        assert entry is not None
        assert entry.name == "test_tool"
        assert entry.toolset == "test"
        assert entry.description == "A test tool"

    def test_register_idempotent(self):
        registry.register(
            name="tool_a",
            toolset="test",
            schema=_make_schema("tool_a", "version 1"),
            handler=_dummy_handler,
        )
        registry.register(
            name="tool_a",
            toolset="test",
            schema=_make_schema("tool_a", "version 2"),
            handler=_dummy_handler,
        )
        entry = registry.get("tool_a")
        assert entry.schema["description"] == "version 2"

    def test_unregister(self):
        registry.register(
            name="tool_b",
            toolset="test",
            schema=_make_schema("tool_b"),
            handler=_dummy_handler,
        )
        assert registry.unregister("tool_b") is True
        assert registry.get("tool_b") is None
        assert registry.unregister("tool_b") is False

    def test_get_nonexistent(self):
        assert registry.get("no_such_tool") is None


class TestToolsets:
    def test_resolve_toolset(self):
        registry.register(name="t1", toolset="web", schema=_make_schema("t1"), handler=_dummy_handler)
        registry.register(name="t2", toolset="web", schema=_make_schema("t2"), handler=_dummy_handler)
        registry.register(name="t3", toolset="text", schema=_make_schema("t3"), handler=_dummy_handler)

        web_tools = registry.resolve_toolset("web")
        assert web_tools == {"t1", "t2"}

        text_tools = registry.resolve_toolset("text")
        assert text_tools == {"t3"}

    def test_resolve_all(self):
        registry.register(name="t1", toolset="web", schema=_make_schema("t1"), handler=_dummy_handler)
        registry.register(name="t2", toolset="text", schema=_make_schema("t2"), handler=_dummy_handler)

        all_tools = registry.resolve_toolset("all")
        assert all_tools == {"t1", "t2"}

        star_tools = registry.resolve_toolset("*")
        assert star_tools == {"t1", "t2"}

    def test_resolve_empty_toolset(self):
        assert registry.resolve_toolset("nonexistent") == set()

    def test_list_toolsets(self):
        registry.register(name="t1", toolset="web", schema=_make_schema("t1"), handler=_dummy_handler)
        registry.register(name="t2", toolset="text", schema=_make_schema("t2"), handler=_dummy_handler)

        toolsets = registry.list_toolsets()
        assert "web" in toolsets
        assert "text" in toolsets
        assert toolsets["web"] == ["t1"]


class TestAvailability:
    def test_check_fn_gates_tool(self):
        registry.register(
            name="gated",
            toolset="test",
            schema=_make_schema("gated"),
            handler=_dummy_handler,
            check_fn=lambda: False,
        )
        tools = registry.get_available_tools()
        names = [t["function"]["name"] for t in tools]
        assert "gated" not in names

    def test_check_fn_allows_tool(self):
        registry.register(
            name="available",
            toolset="test",
            schema=_make_schema("available"),
            handler=_dummy_handler,
            check_fn=lambda: True,
        )
        tools = registry.get_available_tools()
        names = [t["function"]["name"] for t in tools]
        assert "available" in names

    def test_byok_gating(self):
        registry.register(
            name="byok_tool",
            toolset="openai",
            schema=_make_schema("byok_tool"),
            handler=_dummy_handler,
            requires_byok=True,
        )

        # Without BYOK
        tools = registry.get_available_tools()
        names = [t["function"]["name"] for t in tools]
        assert "byok_tool" not in names

        # With BYOK for 'openai'
        tools = registry.get_available_tools(user_has_byok_for={"openai"})
        names = [t["function"]["name"] for t in tools]
        assert "byok_tool" in names

    def test_disabled_tools(self):
        registry.register(name="t1", toolset="test", schema=_make_schema("t1"), handler=_dummy_handler)
        registry.register(name="t2", toolset="test", schema=_make_schema("t2"), handler=_dummy_handler)

        tools = registry.get_available_tools(disabled_tools=["t1"])
        names = [t["function"]["name"] for t in tools]
        assert "t1" not in names
        assert "t2" in names

    def test_enabled_toolsets_filter(self):
        registry.register(name="web1", toolset="web", schema=_make_schema("web1"), handler=_dummy_handler)
        registry.register(
            name="text1", toolset="text", schema=_make_schema("text1"), handler=_dummy_handler
        )

        tools = registry.get_available_tools(enabled_toolsets=["web"])
        names = [t["function"]["name"] for t in tools]
        assert "web1" in names
        assert "text1" not in names


class TestDispatch:
    def test_dispatch_success(self):
        def add_handler(args, **kwargs):
            return {"sum": args.get("a", 0) + args.get("b", 0)}

        registry.register(
            name="add", toolset="math", schema=_make_schema("add"), handler=add_handler
        )
        result = json.loads(registry.dispatch("add", {"a": 3, "b": 4}))
        assert result["sum"] == 7

    def test_dispatch_unknown_tool(self):
        result = json.loads(registry.dispatch("no_such_tool", {}))
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_dispatch_unavailable_tool(self):
        registry.register(
            name="offline",
            toolset="test",
            schema=_make_schema("offline"),
            handler=_dummy_handler,
            check_fn=lambda: False,
        )
        result = json.loads(registry.dispatch("offline", {}))
        assert "error" in result
        assert "not currently available" in result["error"]

    def test_dispatch_handler_exception(self):
        def bad_handler(args, **kwargs):
            raise RuntimeError("boom")

        registry.register(
            name="bad", toolset="test", schema=_make_schema("bad"), handler=bad_handler
        )
        result = json.loads(registry.dispatch("bad", {}))
        assert "error" in result
        assert "boom" in result["error"]

    def test_dispatch_returns_string(self):
        def str_handler(args, **kwargs):
            return "plain text result"

        registry.register(
            name="str_tool", toolset="test", schema=_make_schema("str_tool"), handler=str_handler
        )
        result = registry.dispatch("str_tool", {})
        assert result == "plain text result"


class TestListTools:
    def test_list_tools(self):
        registry.register(
            name="t1",
            toolset="web",
            schema=_make_schema("t1"),
            handler=_dummy_handler,
            description="Tool one",
        )
        registry.register(
            name="t2",
            toolset="text",
            schema=_make_schema("t2"),
            handler=_dummy_handler,
            description="Tool two",
            requires_byok=True,
        )

        tools = registry.list_tools()
        assert len(tools) == 2
        t1 = next(t for t in tools if t["name"] == "t1")
        assert t1["toolset"] == "web"
        assert t1["requires_byok"] is False
        t2 = next(t for t in tools if t["name"] == "t2")
        assert t2["requires_byok"] is True
