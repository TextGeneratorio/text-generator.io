"""Subagent delegation — spawn isolated child tasks with restricted toolsets.

Inspired by Hermes Agent's delegation pattern. Children get:
- Independent iteration budgets
- Restricted toolsets (no delegation, no memory writes)
- Their own conversation context
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Tools that subagents are never allowed to use
BLOCKED_TOOLS = {"delegate_task", "cron_create", "cron_delete", "skill_create", "skill_delete"}

MAX_CONCURRENT_CHILDREN = 3
MAX_DEPTH = 2
DEFAULT_MAX_ITERATIONS = 10


async def run_subagent(
    goal: str,
    context: Optional[str],
    chat_fn,
    tools_enabled: Optional[List[str]] = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    depth: int = 0,
) -> Dict[str, Any]:
    """Run an isolated subagent to completion.

    Args:
        goal: What the subagent should accomplish
        context: Additional background information
        chat_fn: Async callable(messages, tools, max_tokens) -> response dict
        tools_enabled: Which tools the subagent can use
        max_iterations: Max tool-calling iterations
        depth: Current delegation depth

    Returns:
        Dict with task_id, status, result, tool_calls_made, iterations_used
    """
    if depth >= MAX_DEPTH:
        return {
            "task_id": str(uuid.uuid4()),
            "status": "error",
            "result": "Maximum delegation depth exceeded",
            "tool_calls_made": [],
            "iterations_used": 0,
        }

    task_id = str(uuid.uuid4())

    # Build the subagent's system message
    system_content = (
        "You are a focused subagent working on a specific delegated task.\n\n"
        f"YOUR TASK:\n{goal}\n"
    )
    if context:
        system_content += f"\nCONTEXT:\n{context}\n"
    system_content += (
        "\nComplete this task using available tools. When finished, provide a clear summary of:\n"
        "- What you did\n"
        "- What you found/accomplished\n"
        "- Any issues encountered"
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": goal},
    ]

    # Filter out blocked tools
    if tools_enabled:
        tools_enabled = [t for t in tools_enabled if t not in BLOCKED_TOOLS]

    tool_calls_made = []
    iterations = 0

    from questions.agent.registry import registry

    available_tools = registry.get_available_tools(
        enabled_toolsets=None,
        disabled_tools=list(BLOCKED_TOOLS),
    )

    # If specific tools requested, filter further
    if tools_enabled:
        available_tools = [t for t in available_tools if t["function"]["name"] in tools_enabled]

    for iteration in range(max_iterations):
        iterations = iteration + 1

        try:
            response = await chat_fn(
                messages=messages,
                tools=available_tools if available_tools else None,
                max_tokens=2048,
            )
        except Exception as e:
            logger.exception(f"Subagent {task_id} API call failed")
            return {
                "task_id": task_id,
                "status": "error",
                "result": f"API call failed: {str(e)}",
                "tool_calls_made": tool_calls_made,
                "iterations_used": iterations,
            }

        # Extract response
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "stop")

        messages.append(message)

        # If no tool calls, we're done
        if finish_reason != "tool_calls" or not message.get("tool_calls"):
            return {
                "task_id": task_id,
                "status": "completed",
                "result": message.get("content", ""),
                "tool_calls_made": tool_calls_made,
                "iterations_used": iterations,
            }

        # Execute tool calls
        for tc in message["tool_calls"]:
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                fn_args = {}

            if fn_name in BLOCKED_TOOLS:
                result = json.dumps({"error": f"Tool '{fn_name}' is not available to subagents"})
            else:
                result = registry.dispatch(fn_name, fn_args)

            tool_calls_made.append(
                {
                    "tool_call_id": tc["id"],
                    "name": fn_name,
                    "arguments": fn_args,
                    "result": result[:10000],  # Truncate large results
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result[:10000],
                }
            )

        # Budget pressure signaling
        if iterations >= max_iterations * 0.9:
            messages.append(
                {
                    "role": "system",
                    "content": "[Budget warning: provide your final response NOW]",
                }
            )
        elif iterations >= max_iterations * 0.7:
            messages.append(
                {
                    "role": "system",
                    "content": "[Budget caution: start consolidating your work]",
                }
            )

    return {
        "task_id": task_id,
        "status": "completed",
        "result": "Max iterations reached. " + (messages[-1].get("content", "") if messages else ""),
        "tool_calls_made": tool_calls_made,
        "iterations_used": iterations,
    }
