#!/usr/bin/env python3
"""Synthetic contract probes for text-generator.io, OmniServe, and RA1."""

from __future__ import annotations

import argparse
import base64
import binascii
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

TEXT = "Hi i'm bored so looking"
AUTOCOMPLETE_PAYLOAD = {
    "text": TEXT,
    "stop_sequences": [],
    "number_of_results": 1,
    "max_length": 100,
    "max_sentences": 1,
    "min_probability": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "temperature": 0.7,
    "repetition_penalty": 1.17,
    "seed": 0,
    "model": "best",
    "enable_thinking": False,
    "system_message": "",
}
EMBEDDING_TEXT = "monitor embeddings"
FEATURE_EXTRACTION_PAYLOAD = {"text": EMBEDDING_TEXT, "num_features": 768}
OPENAI_EMBEDDING_PAYLOAD = {
    "input": EMBEDDING_TEXT,
    "model": "omniserve-modernbert",
    "dimensions": 768,
}
OPENAI_EMBEDDING_BATCH = ["monitor embeddings one", "monitor embeddings two"]
MONITOR_IMAGE_PATH = Path(__file__).resolve().parent.parent / "static/icons/android-chrome-192x192.png"
CORE_TEXT_TIMEOUT = 45.0


@dataclass
class ProbeResult:
    name: str
    ok: bool
    elapsed_ms: int
    detail: str
    status: int | None = None


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[int, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {
        "accept": "application/json",
        "user-agent": "text-generator-production-monitor/1.0",
        **(headers or {}),
    }
    if body is not None:
        request_headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=request_headers)
    try:
        with opener(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        try:
            parsed = json.loads(exc.read())
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed = {"error": "non-JSON HTTP error"}
        return exc.code, parsed


def _request_image_caption(
    url: str,
    *,
    secret: str | None = None,
    timeout: float = 120.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[int, Any]:
    boundary = "----text-generator-caption-monitor"
    image = MONITOR_IMAGE_PATH.read_bytes()
    parts = [
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="fast_mode"\r\n\r\n'
            "true\r\n"
        ).encode(),
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="image_file"; filename="monitor.png"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode()
        + image
        + b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    headers = {
        "accept": "application/json",
        "content-type": f"multipart/form-data; boundary={boundary}",
        "user-agent": "text-generator-production-monitor/1.0",
    }
    if secret:
        headers["secret"] = secret
    request = urllib.request.Request(url, data=b"".join(parts), headers=headers)
    try:
        with opener(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        try:
            parsed = json.loads(exc.read())
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed = {"error": "non-JSON HTTP error"}
        return exc.code, parsed


def _validate_completion(body: Any) -> str | None:
    if not isinstance(body, list) or len(body) != 1 or not isinstance(body[0], dict):
        return "response must be a one-item JSON array"
    generated = body[0].get("generated_text")
    if not isinstance(generated, str) or not generated.startswith(TEXT):
        return "generated_text must preserve the prompt prefix"
    continuation = generated[len(TEXT) :]
    if len(continuation) < 2 or not continuation[0].isspace() or not continuation.strip():
        return "continuation must begin at a word boundary and contain text"
    if not isinstance(body[0].get("stop_reason"), str):
        return "stop_reason must be present"
    return None


def probe_completion(
    name: str,
    url: str,
    *,
    secret: str | None = None,
    timeout: float = 15.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    started = time.monotonic()
    try:
        headers = {"secret": secret} if secret else None
        status, body = _request_json(
            url,
            payload=AUTOCOMPLETE_PAYLOAD,
            headers=headers,
            timeout=timeout,
            opener=opener,
        )
        contract_error = _validate_completion(body) if status == 200 else None
        ok = status == 200 and contract_error is None
        detail = contract_error or ("contract ok" if ok else f"HTTP {status}")
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_feature_extraction(
    name: str,
    url: str,
    *,
    secret: str | None = None,
    dimensions: int = 768,
    timeout: float = 15.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    started = time.monotonic()
    try:
        headers = {"secret": secret} if secret else None
        status, body = _request_json(
            url,
            payload={**FEATURE_EXTRACTION_PAYLOAD, "num_features": dimensions},
            headers=headers,
            timeout=timeout,
            opener=opener,
        )
        valid = (
            isinstance(body, list)
            and len(body) == dimensions
            and all(_is_finite_number(value) for value in body)
        )
        ok = status == 200 and valid
        detail = f"{dimensions}-dimension contract ok" if ok else f"HTTP {status} or invalid vector"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_openai_embeddings(
    name: str,
    url: str,
    *,
    secret: str | None = None,
    dimensions: int = 768,
    timeout: float = 15.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    started = time.monotonic()
    try:
        headers = {"secret": secret} if secret else None
        status, body = _request_json(
            url,
            payload={**OPENAI_EMBEDDING_PAYLOAD, "dimensions": dimensions},
            headers=headers,
            timeout=timeout,
            opener=opener,
        )
        data = body.get("data") if isinstance(body, dict) else None
        embedding = data[0].get("embedding") if isinstance(data, list) and len(data) == 1 else None
        valid = (
            body.get("object") == "list"
            and isinstance(embedding, list)
            and len(embedding) == dimensions
            and all(_is_finite_number(value) for value in embedding)
        ) if isinstance(body, dict) else False
        ok = status == 200 and valid
        detail = f"OpenAI {dimensions}-dimension contract ok" if ok else f"HTTP {status} or invalid contract"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_openai_embedding_batch(
    name: str,
    url: str,
    *,
    secret: str | None = None,
    dimensions: int = 64,
    timeout: float = 15.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    started = time.monotonic()
    try:
        headers = {"secret": secret} if secret else None
        status, body = _request_json(
            url,
            payload={
                **OPENAI_EMBEDDING_PAYLOAD,
                "input": OPENAI_EMBEDDING_BATCH,
                "dimensions": dimensions,
            },
            headers=headers,
            timeout=timeout,
            opener=opener,
        )
        data = body.get("data") if isinstance(body, dict) else None
        valid = (
            body.get("object") == "list"
            and isinstance(data, list)
            and len(data) == len(OPENAI_EMBEDDING_BATCH)
            and all(
                isinstance(item, dict)
                and item.get("index") == index
                and isinstance(item.get("embedding"), list)
                and len(item["embedding"]) == dimensions
                and all(_is_finite_number(value) for value in item["embedding"])
                for index, item in enumerate(data)
            )
        ) if isinstance(body, dict) else False
        ok = status == 200 and valid
        detail = f"OpenAI batch {len(OPENAI_EMBEDDING_BATCH)}x{dimensions} contract ok" if ok else f"HTTP {status} or invalid batch contract"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_json_get(
    name: str,
    url: str,
    *,
    required_key: str | None = None,
    timeout: float = 10.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    started = time.monotonic()
    try:
        status, body = _request_json(url, timeout=timeout, opener=opener)
        key_ok = required_key is None or isinstance(body, dict) and required_key in body
        ok = status == 200 and key_ok
        detail = "JSON contract ok" if ok else f"HTTP {status} or missing {required_key}"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_lora_catalog(
    name: str = "omniserve-native:loras",
    url: str = "http://127.0.0.1:8791/loras",
    *,
    timeout: float = 10.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    """Require the live Z-Image worker's non-empty LoRA catalog."""
    started = time.monotonic()
    try:
        status, body = _request_json(url, timeout=timeout, opener=opener)
        loras = body.get("loras") if isinstance(body, dict) else None
        count = body.get("count") if isinstance(body, dict) else None
        valid = (
            isinstance(loras, list)
            and bool(loras)
            and isinstance(count, int)
            and count == len(loras)
            and all(isinstance(item, dict) and isinstance(item.get("id"), str)
                    and bool(item["id"]) for item in loras)
        )
        ok = status == 200 and valid
        detail = (
            f"Z-Image LoRA catalog ok ({count} adapters)"
            if ok else f"HTTP {status} or invalid/empty LoRA catalog"
        )
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def _monitor_wav_base64() -> str:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 4000)
    return base64.b64encode(output.getvalue()).decode("ascii")


def probe_gemma_multimodal_chat(
    name: str = "omniserve-native:gemma-multimodal-chat",
    url: str = "http://127.0.0.1:8791/v1/chat/completions",
    *,
    secret: str | None = None,
    timeout: float = 900.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    """Exercise standard OpenAI image+audio content through OmniServe Native."""
    started = time.monotonic()
    try:
        image = base64.b64encode(MONITOR_IMAGE_PATH.read_bytes()).decode("ascii")
        status, body = _request_json(
            url,
            payload={
                "model": "google/gemma-4-e4b-it",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image}"},
                            },
                            {
                                "type": "input_audio",
                                "input_audio": {"data": _monitor_wav_base64(), "format": "wav"},
                            },
                            {"type": "input_text", "text": "Briefly confirm both inputs were received."},
                        ],
                    }
                ],
                "max_tokens": 8,
                "temperature": 0,
                "stream": False,
            },
            headers={"secret": secret} if secret else None,
            timeout=timeout,
            opener=opener,
        )
        choices = body.get("choices") if isinstance(body, dict) else None
        message = choices[0].get("message") if isinstance(choices, list) and choices else None
        content = message.get("content") if isinstance(message, dict) else None
        ok = status == 200 and isinstance(content, str) and bool(content.strip())
        detail = "Gemma image+audio OpenAI contract ok" if ok else f"HTTP {status} or invalid chat contract"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_image_caption(
    name: str,
    url: str,
    *,
    secret: str | None = None,
    timeout: float = 120.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    started = time.monotonic()
    try:
        status, body = _request_image_caption(
            url,
            secret=secret,
            timeout=timeout,
            opener=opener,
        )
        valid = (
            isinstance(body, dict)
            and isinstance(body.get("caption"), str)
            and bool(body["caption"].strip())
            and body.get("model") == "microsoft/git-base"
            and body.get("fast_mode") is True
        )
        ok = status == 200 and valid
        detail = "Git-base caption contract ok" if ok else f"HTTP {status} or invalid caption contract"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_omniserve_caption(
    name: str = "omniserve:caption",
    url: str = "http://127.0.0.1:8790/v1/images/captions",
    *,
    timeout: float = 120.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    started = time.monotonic()
    try:
        status, body = _request_json(
            url,
            payload={
                "model": "git-base-caption",
                "image": base64.b64encode(MONITOR_IMAGE_PATH.read_bytes()).decode("ascii"),
                "max_new_tokens": 10,
            },
            timeout=timeout,
            opener=opener,
        )
        data = body.get("data") if isinstance(body, dict) else None
        text = data[0].get("text") if isinstance(data, list) and data else None
        valid = body.get("model") == "git-base-caption" and isinstance(text, str) and bool(text.strip()) \
            if isinstance(body, dict) else False
        ok = status == 200 and valid
        detail = "OmniServe Git-base contract ok" if ok else f"HTTP {status} or invalid caption contract"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_classification(
    name: str,
    url: str,
    *,
    image: bool,
    timeout: float = 120.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    """Exercise CLIP inference, not merely its model/status registration."""
    started = time.monotonic()
    labels = ["application icon", "landscape photograph"]
    payload: dict[str, Any] = {"model": "clip-vit-large", "labels": labels}
    if image:
        payload["image"] = base64.b64encode(MONITOR_IMAGE_PATH.read_bytes()).decode("ascii")
    else:
        payload["input"] = "a small application icon"
    try:
        status, body = _request_json(
            url, payload=payload, timeout=timeout, opener=opener
        )
        data = body.get("data") if isinstance(body, dict) else None
        first = data[0] if isinstance(data, list) and data else None
        valid = (
            body.get("model") == "clip-vit-large"
            and body.get("labels") == labels
            and isinstance(first, dict)
            and first.get("label") in labels
            and isinstance(first.get("scores"), list)
            and bool(first["scores"])
        ) if isinstance(body, dict) else False
        ok = status == 200 and valid
        detail = "CLIP classification contract ok" if ok else f"HTTP {status} or invalid classification contract"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_image_generation(
    name: str = "omniserve-native:image-generation",
    url: str = "http://127.0.0.1:8791/v1/images/generations",
    *,
    lora_id: str | None = None,
    timeout: float = 240.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    """Generate one deliberately small local image and validate OpenAI shape."""
    started = time.monotonic()
    try:
        payload = {
            "prompt": "monitoring probe: a simple blue circle on white",
            "size": "512x512",
            "steps": 4,
            "seed": 20260804,
        }
        if lora_id:
            payload.update({
                "prompt": "360panorama, monitoring probe: a simple mountain lake",
                "lora_id": lora_id,
                "lora_scale": 1.0,
                "auto_lora": False,
            })
        status, body = _request_json(
            url,
            payload=payload,
            timeout=timeout,
            opener=opener,
        )
        data = body.get("data") if isinstance(body, dict) else None
        encoded = data[0].get("b64_json") if isinstance(data, list) and data and isinstance(data[0], dict) else None
        valid = isinstance(encoded, str) and len(encoded) > 100
        if valid:
            try:
                raw = base64.b64decode(encoded, validate=True)
                valid = (
                    raw.startswith(b"\x89PNG")
                    or raw.startswith(b"\xff\xd8\xff")
                    or (raw.startswith(b"RIFF") and raw[8:12] == b"WEBP")
                )
            except (binascii.Error, ValueError):
                valid = False
        ok = status == 200 and valid
        detail = (
            f"Z-Image LoRA generation contract ok ({lora_id})"
            if ok and lora_id
            else "Z-Image generation contract ok"
            if ok
            else f"HTTP {status} or invalid image contract"
        )
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def probe_background_removal(
    name: str = "omniserve-native:background-removal",
    url: str = "http://127.0.0.1:8791/v1/images/background-removals",
    *,
    timeout: float = 180.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> ProbeResult:
    """Run the CPU BiRefNet worker and require a real transparent WebP."""
    started = time.monotonic()
    status: int | None = None
    try:
        source = base64.b64encode(MONITOR_IMAGE_PATH.read_bytes()).decode("ascii")
        request = urllib.request.Request(
            url,
            data=json.dumps({
                "image_url": f"data:image/png;base64,{source}",
                "output_format": "webp",
            }).encode("utf-8"),
            headers={"accept": "image/webp", "content-type": "application/json"},
        )
        with opener(request, timeout=timeout) as response:
            status = response.status
            body = response.read()
            content_type = response.headers.get("content-type", "")
        valid = (
            content_type.startswith("image/webp")
            and body.startswith(b"RIFF")
            and body[8:12] == b"WEBP"
            and len(body) > 100
        )
        ok = status == 200 and valid
        detail = "BiRefNet WebP contract ok" if ok else f"HTTP {status} or invalid WebP contract"
    except urllib.error.HTTPError as exc:
        status = exc.code
        ok = False
        detail = f"HTTP {status}"
    except Exception as exc:
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult(name, ok, int((time.monotonic() - started) * 1000), detail, status)


def _port_owner_pids(expected_port: int) -> tuple[bool, list[str]]:
    sockets = subprocess.run(
        ["ss", "-H", "-ltnp"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    port_lines = [
        line for line in sockets.stdout.splitlines()
        if re.search(rf":{expected_port}\s", line)
    ]
    owner_pids = sorted({
        match
        for line in port_lines
        for match in re.findall(r"pid=(\d+)", line)
    })
    return sockets.returncode == 0, owner_pids


def _pid_cgroup(pid: str) -> str:
    try:
        return Path(f"/proc/{pid}/cgroup").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _pids_in_service_cgroup(pids: list[str], unit: str) -> list[str]:
    needle = f"/system.slice/{unit}"
    return [pid for pid in pids if needle in _pid_cgroup(pid)]


def probe_systemd_service(unit: str, *, expected_port: int | None = None) -> ProbeResult:
    started = time.monotonic()
    try:
        process = subprocess.run(
            ["systemctl", "show", unit, "--property=ActiveState,SubState,MainPID"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        values = dict(
            line.split("=", 1)
            for line in process.stdout.splitlines()
            if "=" in line
        )
        active = values.get("ActiveState", "")
        sub = values.get("SubState", "")
        pid = values.get("MainPID", "")
        ok = process.returncode == 0 and active == "active" and sub == "running" and pid not in {"", "0"}
        detail = f"active={active or 'unknown'} sub={sub or 'unknown'} main_pid={pid or 'unknown'}"
    except subprocess.TimeoutExpired as exc:
        active = sub = pid = ""
        ok = False
        detail = f"systemctl=timeout after {exc.timeout:g}s"
    except Exception as exc:
        active = sub = pid = ""
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"

    if expected_port is not None:
        try:
            sockets_ok, owner_pids = _port_owner_pids(expected_port)
            service_pids = _pids_in_service_cgroup(owner_pids, unit)
            owns_port = bool(owner_pids) and (
                pid in owner_pids
                or service_pids == owner_pids
            )
            if not active and not sub and not pid:
                ok = sockets_ok and owns_port
            else:
                ok = ok and sockets_ok and owns_port
            detail += (
                f" port={expected_port} owner_pids={','.join(owner_pids) or 'none'}"
                f" service_cgroup_pids={','.join(service_pids) or 'none'}"
            )
        except Exception as exc:
            ok = False
            detail += f" port={expected_port} socket_check={type(exc).__name__}: {str(exc)[:120]}"

    return ProbeResult(f"systemd:{unit}", ok, int((time.monotonic() - started) * 1000), detail)


def probe_ra1_generation(api_key: str) -> ProbeResult:
    started = time.monotonic()
    payload = {
        "api_key": api_key,
        "prompt": "RA1 monitoring probe: a small blue ceramic bird on a plain studio background",
        "resolution": "1024x1024",
        "num_images": 1,
    }
    try:
        status, body = _request_json(
            os.getenv("RA1_MONITOR_GENERATE_URL", "https://ra.netwrck.com/api/ra1"),
            payload=payload,
            timeout=180.0,
        )
        images = body.get("images") if isinstance(body, dict) else None
        ok = status == 200 and body.get("success") is True and isinstance(images, list) and bool(images)
        detail = "image contract ok" if ok else f"HTTP {status}; success/image contract failed"
    except Exception as exc:
        status = None
        ok = False
        detail = f"{type(exc).__name__}: {str(exc)[:180]}"
    return ProbeResult("ra1:generation", ok, int((time.monotonic() - started) * 1000), detail, status)


def run_checks(profile: str = "core", *, include_ra1_generation: bool = False) -> list[ProbeResult]:
    secret = os.getenv("TEXTGEN_MONITOR_SECRET")
    caption_secret = (
        os.getenv("NETWRCK_IMAGE_CAPTION_SECRET")
        or secret
        or os.getenv("TEXT_GENERATOR_API_KEY")
    )
    chat_secret = (
        os.getenv("NETWRCK_PARTNER_SECRET")
        or secret
        or os.getenv("TEXT_GENERATOR_API_KEY")
    )
    if profile == "caption":
        return [
            probe_systemd_service("omniserve.service", expected_port=8790),
            probe_omniserve_caption(),
            probe_image_caption(
                "compat:image-caption",
                "http://127.0.0.1:9083/api/v1/image-caption",
                secret=caption_secret,
            ),
            probe_image_caption(
                "omniserve-native:image-caption",
                "http://127.0.0.1:8791/api/v1/image-caption",
                secret=caption_secret,
            ),
            probe_image_caption(
                "production:image-caption",
                "https://api.text-generator.io/api/v1/image-caption",
                secret=caption_secret,
            ),
        ]
    if profile == "parity":
        return [
            *run_checks("core"),
            *run_checks("caption"),
            probe_systemd_service("omniserve-asr-router.service", expected_port=9096),
            probe_systemd_service("omniserve-3d-worker.service", expected_port=9093),
            probe_systemd_service("omniserve-training-manager.service", expected_port=9098),
            probe_systemd_service("omniserve-birefnet-worker.service", expected_port=9094),
            probe_json_get("asr-router:health", "http://127.0.0.1:9096/health", required_key="status"),
            probe_json_get("3d-worker:health", "http://127.0.0.1:9093/health", required_key="status"),
            probe_json_get("training:health", "http://127.0.0.1:9098/health", required_key="status"),
            probe_json_get("birefnet:health", "http://127.0.0.1:9094/health", required_key="status"),
            probe_json_get("omniserve-native:training-status", "http://127.0.0.1:8791/v1/training/status", required_key="jobs"),
            probe_lora_catalog(),
            probe_gemma_multimodal_chat(secret=chat_secret),
            probe_omniserve_caption(
                "omniserve-native:direct-caption",
                "http://127.0.0.1:8791/v1/images/captions",
            ),
            probe_classification(
                "omniserve-native:image-classification",
                "http://127.0.0.1:8791/v1/images/classifications",
                image=True,
            ),
            probe_classification(
                "omniserve-native:text-classification",
                "http://127.0.0.1:8791/v1/classifications",
                image=False,
            ),
            probe_image_generation(
                name="omniserve-native:lora-image-generation",
                lora_id="zimage_360",
            ),
            # A base render immediately afterwards also verifies that the
            # worker can deactivate the synthetic adapter cleanly.
            probe_image_generation(),
            probe_background_removal(),
        ]
    if profile == "all":
        results = run_checks("parity")
        results.extend(
            [
                probe_json_get(
                    "ra1:pricing",
                    "https://ra.netwrck.com/api/ra1/pricing",
                    required_key="base_price_cents",
                ),
                probe_json_get(
                    "ra1:search",
                    "https://ra.netwrck.com/api/ra1/search?q=monitoring",
                    required_key="results",
                ),
            ]
        )
        if include_ra1_generation:
            key = os.getenv("RA1_MONITOR_API_KEY")
            if key:
                results.append(probe_ra1_generation(key))
            else:
                results.append(ProbeResult("ra1:generation", False, 0, "RA1_MONITOR_API_KEY is not set"))
        return results
    results = [
        probe_systemd_service("omniserve.service", expected_port=8790),
        probe_systemd_service("omniserve-native.service", expected_port=8791),
        probe_systemd_service("text-generator-inference.service", expected_port=9083),
        probe_completion(
            "omniserve-native:generate",
            "http://127.0.0.1:8791/api/v1/generate",
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_completion(
            "compat:generate",
            "http://127.0.0.1:9083/api/v1/generate",
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_completion(
            "production:generate",
            "https://api.text-generator.io/api/v1/generate",
            secret=secret,
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_completion(
            "production:autocomplete",
            "https://api.text-generator.io/api/v1/autocomplete",
            secret=secret,
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_feature_extraction(
            "omniserve-native:feature-extraction",
            "http://127.0.0.1:8791/api/v1/feature-extraction",
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_feature_extraction(
            "compat:feature-extraction",
            "http://127.0.0.1:9083/api/v1/feature-extraction",
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_feature_extraction(
            "production:feature-extraction",
            "https://api.text-generator.io/api/v1/feature-extraction",
            secret=secret,
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_openai_embeddings(
            "omniserve-native:openai-embeddings",
            "http://127.0.0.1:8791/v1/embeddings",
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_openai_embeddings(
            "compat:openai-embeddings",
            "http://127.0.0.1:9083/v1/embeddings",
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_openai_embeddings(
            "production:openai-embeddings",
            "https://api.text-generator.io/v1/embeddings",
            secret=secret,
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_openai_embedding_batch(
            "omniserve-native:openai-embedding-batch",
            "http://127.0.0.1:8791/v1/embeddings",
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_openai_embedding_batch(
            "compat:openai-embedding-batch",
            "http://127.0.0.1:9083/v1/embeddings",
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_openai_embedding_batch(
            "production:openai-embedding-batch",
            "https://api.text-generator.io/v1/embeddings",
            secret=secret,
            timeout=CORE_TEXT_TIMEOUT,
        ),
        probe_json_get(
            "omniserve:status",
            "http://127.0.0.1:8790/status",
            required_key="backends",
        ),
        probe_json_get(
            "production:native-status",
            "https://api.text-generator.io/status",
            required_key="llm",
        ),
        probe_json_get(
            "production:speech-catalog",
            "https://api.text-generator.io/api/v1/speech/catalog",
            required_key="providers",
        ),
    ]
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("core", "all", "caption", "parity"), default="core")
    parser.add_argument("--include-ra1-generation", action="store_true")
    args = parser.parse_args()
    results = run_checks(args.profile, include_ra1_generation=args.include_ra1_generation)
    print(json.dumps({"ok": all(item.ok for item in results), "results": [asdict(item) for item in results]}))
    return 0 if all(item.ok for item in results) else 1


if __name__ == "__main__":
    sys.exit(main())
