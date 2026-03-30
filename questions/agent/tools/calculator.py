"""Calculator tool — safe math evaluation (no API cost)."""

import json
import math

from questions.agent.registry import registry

# Safe math functions available
SAFE_MATH = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
}


def calculator_handler(args: dict, **kwargs) -> str:
    """Evaluate a mathematical expression safely."""
    expression = args.get("expression", "")
    if not expression:
        return json.dumps({"error": "No expression provided"})

    try:
        # Only allow safe builtins
        result = eval(expression, {"__builtins__": {}}, SAFE_MATH)  # noqa: S307
        return json.dumps({"result": result, "expression": expression})
    except Exception as e:
        return json.dumps({"error": f"Invalid expression: {str(e)}"})


SCHEMA = {
    "name": "calculator",
    "description": "Evaluate a mathematical expression. Supports basic arithmetic and math functions (sqrt, log, sin, cos, etc.).",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate, e.g. 'sqrt(144) + 2 * pi'",
            },
        },
        "required": ["expression"],
    },
}

registry.register(
    name="calculator",
    toolset="utility",
    schema=SCHEMA,
    handler=calculator_handler,
    description="Evaluate mathematical expressions",
)
