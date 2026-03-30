"""Summarization tool — condense text to key points."""

import json
import os

from questions.agent.registry import registry

INFERENCE_URL = os.getenv("INFERENCE_SERVER_URL", "https://api.text-generator.io")


def _check_available() -> bool:
    return True


def summarize_handler(args: dict, **kwargs) -> str:
    """Summarize text using the inference server."""
    text = args.get("text", "")
    max_length = args.get("max_length", 150)

    if not text:
        return json.dumps({"error": "No text provided"})

    if len(text) < 50:
        return json.dumps({"summary": text, "note": "Text too short to summarize"})

    import requests

    secret = kwargs.get("user_secret", "")
    prompt = f"Summarize the following text concisely:\n\n{text[:4000]}\n\nSummary:"

    try:
        resp = requests.post(
            f"{INFERENCE_URL}/api/v1/generate",
            json={
                "text": prompt,
                "max_length": max_length,
                "temperature": 0.3,
                "number_of_results": 1,
                "top_p": 0.9,
            },
            headers={"secret": secret, "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return json.dumps({"summary": resp.json(), "original_length": len(text)})
    except Exception as e:
        return json.dumps({"error": f"Summarization failed: {str(e)}"})


SCHEMA = {
    "name": "summarize",
    "description": "Summarize long text into a concise summary.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to summarize"},
            "max_length": {
                "type": "integer",
                "description": "Maximum summary length in tokens (default 150)",
                "default": 150,
            },
        },
        "required": ["text"],
    },
}

registry.register(
    name="summarize",
    toolset="text",
    schema=SCHEMA,
    handler=summarize_handler,
    description="Summarize text into key points",
    check_fn=_check_available,
)
