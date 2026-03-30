"""Text generation tool — uses our own inference server."""

import json
import os

import requests

from questions.agent.registry import registry

INFERENCE_URL = os.getenv("INFERENCE_SERVER_URL", "https://api.text-generator.io")


def _check_available() -> bool:
    return True  # Always available — uses our own server


def text_generate_handler(args: dict, **kwargs) -> str:
    """Generate text using the inference server."""
    prompt = args.get("prompt", "")
    max_length = args.get("max_length", 200)
    temperature = args.get("temperature", 0.7)

    if not prompt:
        return json.dumps({"error": "No prompt provided"})

    secret = kwargs.get("user_secret", "")

    try:
        resp = requests.post(
            f"{INFERENCE_URL}/api/v1/generate",
            json={
                "text": prompt,
                "max_length": max_length,
                "temperature": temperature,
                "number_of_results": 1,
                "top_p": 0.9,
                "repetition_penalty": 1.2,
            },
            headers={"secret": secret, "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return json.dumps({"generated_text": data, "prompt": prompt})
    except Exception as e:
        return json.dumps({"error": f"Text generation failed: {str(e)}"})


SCHEMA = {
    "name": "text_generate",
    "description": "Generate text continuation from a prompt using the text-generator.io inference server.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "The text prompt to continue"},
            "max_length": {
                "type": "integer",
                "description": "Maximum tokens to generate (default 200)",
                "default": 200,
            },
            "temperature": {
                "type": "number",
                "description": "Sampling temperature (default 0.7)",
                "default": 0.7,
            },
        },
        "required": ["prompt"],
    },
}

registry.register(
    name="text_generate",
    toolset="text",
    schema=SCHEMA,
    handler=text_generate_handler,
    description="Generate text using text-generator.io",
    check_fn=_check_available,
)
