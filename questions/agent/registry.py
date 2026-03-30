"""Tool registry — singleton pattern for registering, discovering, and dispatching tools.

Inspired by Hermes Agent's registry pattern. Each tool self-registers with a schema,
handler, and optional availability check function.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ToolEntry:
    name: str
    toolset: str  # Grouping: 'web', 'text', 'code', 'media', etc.
    schema: Dict[str, Any]  # OpenAI function-calling format
    handler: Callable  # (args: dict, **kwargs) -> str (JSON)
    description: str = ""
    check_fn: Optional[Callable[[], bool]] = None  # Returns True if tool is available
    requires_env: List[str] = field(default_factory=list)
    requires_byok: bool = False  # Requires user's own API key
    is_async: bool = False


# Predefined toolset compositions
TOOLSET_COMPOSITIONS = {
    "research": ["web", "text"],
    "content": ["text", "media"],
    "all": [],  # Resolved dynamically to include everything
}


class ToolRegistry:
    """Singleton registry for all agent tools."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, ToolEntry] = {}
            cls._instance._toolsets: Dict[str, Set[str]] = {}
        return cls._instance

    def register(
        self,
        name: str,
        toolset: str,
        schema: Dict[str, Any],
        handler: Callable,
        description: str = "",
        check_fn: Optional[Callable[[], bool]] = None,
        requires_env: Optional[List[str]] = None,
        requires_byok: bool = False,
        is_async: bool = False,
    ) -> None:
        """Register a tool. Idempotent — re-registering overwrites."""
        entry = ToolEntry(
            name=name,
            toolset=toolset,
            schema=schema,
            handler=handler,
            description=description or schema.get("description", ""),
            check_fn=check_fn,
            requires_env=requires_env or [],
            requires_byok=requires_byok,
            is_async=is_async,
        )
        self._tools[name] = entry
        self._toolsets.setdefault(toolset, set()).add(name)
        logger.debug(f"Registered tool: {name} (toolset={toolset})")

    def unregister(self, name: str) -> bool:
        """Remove a tool. Returns True if it existed."""
        entry = self._tools.pop(name, None)
        if entry:
            self._toolsets.get(entry.toolset, set()).discard(name)
            return True
        return False

    def get(self, name: str) -> Optional[ToolEntry]:
        return self._tools.get(name)

    def resolve_toolset(self, toolset_name: str) -> Set[str]:
        """Resolve a toolset name to a set of tool names, supporting compositions."""
        if toolset_name == "all" or toolset_name == "*":
            return set(self._tools.keys())

        if toolset_name in TOOLSET_COMPOSITIONS:
            result = set()
            for child in TOOLSET_COMPOSITIONS[toolset_name]:
                result |= self.resolve_toolset(child)
            return result

        return set(self._toolsets.get(toolset_name, set()))

    def get_available_tools(
        self,
        enabled_toolsets: Optional[List[str]] = None,
        disabled_tools: Optional[List[str]] = None,
        user_has_byok_for: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get OpenAI-format tool definitions for available tools.

        Args:
            enabled_toolsets: Which toolsets to include (None = all)
            disabled_tools: Specific tools to exclude
            user_has_byok_for: Set of providers the user has BYOK keys for
        """
        disabled = set(disabled_tools or [])
        byok_providers = user_has_byok_for or set()

        # Resolve which tools to consider
        if enabled_toolsets:
            candidates = set()
            for ts in enabled_toolsets:
                candidates |= self.resolve_toolset(ts)
        else:
            candidates = set(self._tools.keys())

        candidates -= disabled
        result = []

        for name in sorted(candidates):
            entry = self._tools.get(name)
            if not entry:
                continue

            # Check availability
            if entry.check_fn and not entry.check_fn():
                continue

            # Check BYOK requirement
            if entry.requires_byok and entry.toolset not in byok_providers:
                continue

            result.append(
                {
                    "type": "function",
                    "function": entry.schema,
                }
            )

        return result

    def dispatch(self, name: str, args: Dict[str, Any], **kwargs) -> str:
        """Execute a tool by name. Returns JSON string."""
        entry = self._tools.get(name)
        if not entry:
            return json.dumps({"error": f"Unknown tool: {name}"})

        if entry.check_fn and not entry.check_fn():
            return json.dumps({"error": f"Tool '{name}' is not currently available"})

        try:
            result = entry.handler(args, **kwargs)
            if isinstance(result, dict):
                return json.dumps(result)
            return str(result)
        except Exception as e:
            logger.exception(f"Tool '{name}' failed")
            return json.dumps({"error": f"Tool '{name}' failed: {str(e)}"})

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with metadata."""
        return [
            {
                "name": entry.name,
                "toolset": entry.toolset,
                "description": entry.description,
                "requires_byok": entry.requires_byok,
                "available": entry.check_fn() if entry.check_fn else True,
            }
            for entry in sorted(self._tools.values(), key=lambda e: e.name)
        ]

    def list_toolsets(self) -> Dict[str, List[str]]:
        """List all toolsets and their tools."""
        result = {}
        for ts_name, tool_names in sorted(self._toolsets.items()):
            result[ts_name] = sorted(tool_names)
        return result

    @classmethod
    def reset(cls):
        """Reset the singleton (for testing)."""
        if cls._instance:
            cls._instance._tools.clear()
            cls._instance._toolsets.clear()


# Module-level singleton
registry = ToolRegistry()
