#!/usr/bin/env python
"""inference_server API parity adapter over a vLLM OpenAI backend.

Exposes the text-generator.io `/api/v1/generate` contract (and `/liveness_check`)
so a fast vLLM-served model (e.g. Gemma-4 E4B) can sit behind the same load
balancer as the existing HF-transformers models. The generation parameter
SEMANTICS mirror questions/text_generator_inference.py's Qwen3.5 chat path:

  - max_length          -> max_new_tokens cap on the response (token-truncate)
  - min_probability     -> product of per-token argmax softmax probs; truncate
                           (inclusive) at the first token where the running
                           product < min_probability  (uses vLLM logprobs)
  - stop_sequences      -> substring match on response text, EXCLUSIVE removal;
                           stop_reason becomes the matched sequence string
  - max_sentences       -> regex [.!?](\\s|$) sentence cap
  - number_of_results   -> N independent samples (vLLM n=N)
  - temperature<=0      -> forced to 1.0, do_sample always on (legacy parity)
  - generated_text      -> original input text + continuation
  - response objects    -> {generated_text, stop_reason, thinking_content}

stop_reason precedence (matches chat_inference order): min_probability and
max_length take priority (they run first / unguarded); stop_sequence and
max_sentences only override a still-"stop" reason.

Run (in the vLLM venv):
  VLLM_BASE=http://127.0.0.1:8200 VLLM_MODEL=gemma-4-e4b-it \\
    uvicorn questions.inference_server.vllm_parity_adapter:app --port 8300
"""
from __future__ import annotations

import json
import math
import os
import re
import urllib.request
from typing import List, Optional

import random
import time

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from questions.inference_server.vllm_backend_manager import from_env as _backend_from_env

VLLM_BASE = os.environ.get("VLLM_BASE", "http://127.0.0.1:8200").rstrip("/")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "gemma-4-e4b-it")
SERVED_NAME = os.environ.get("ADAPTER_MODEL_NAME", VLLM_MODEL)
REQUEST_TIMEOUT = float(os.environ.get("ADAPTER_TIMEOUT", "600"))

# Default system prompt mirrors text_generator_inference's continuation engine.
DEFAULT_SYSTEM = (
    "You are a text continuation engine. Continue the user's text naturally, "
    "matching its tone and style. Do not add commentary or explanations."
)

app = FastAPI(title="vLLM inference_server parity adapter", version="1")

# Optional on-demand backend lifecycle (lazy start + idle-unload to free GPU).
# Disabled (None) when VLLM_BACKEND_CMD is unset -> we just proxy a running server.
BACKEND = _backend_from_env()


def _ensure_backend():
    if BACKEND is not None:
        BACKEND.ensure_up()


def _rand_id(n: int = 10) -> str:
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=n))


class GenerateParams(BaseModel):
    text: str
    number_of_results: int = 1
    max_length: Optional[int] = 100
    min_length: Optional[int] = 1
    max_sentences: Optional[int] = None
    min_probability: Optional[float] = 0.0
    stop_sequences: Optional[List[str]] = []
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    temperature: Optional[float] = 0.7
    seed: Optional[int] = None
    repetition_penalty: Optional[float] = 1.2
    model: Optional[str] = None
    system_message: Optional[str] = None
    system_prompt: Optional[str] = None
    enable_thinking: Optional[bool] = None


# --------------------------------------------------------------------------
# Post-processing (pure reimplementations of the inference_server semantics)
# --------------------------------------------------------------------------

def _split_thinking(text: str) -> tuple[Optional[str], str]:
    """Return (thinking_content_or_None, response_text)."""
    end = text.find("</think>")
    if end == -1:
        return None, text
    head = text[:end]
    start = head.find("<think>")
    thinking = head[start + len("<think>"):] if start != -1 else head
    response = text[end + len("</think>"):]
    return (thinking.strip() or None), response.lstrip("\n")


def _truncate_by_min_probability(argmax_probs: List[float], text_tokens: List[str],
                                 min_probability: float) -> tuple[int, bool]:
    """Return (num_tokens_to_keep, triggered). argmax_probs aligned to tokens."""
    if not min_probability or min_probability <= 0 or not argmax_probs:
        return len(text_tokens), False
    total = None
    for i, p in enumerate(argmax_probs):
        total = p if total is None else total * p
        if total < min_probability:
            return i + 1, True  # inclusive of the offending token
    return len(text_tokens), False


def _truncate_by_stop_sequences(text: str, stop_sequences: List[str]):
    for s in stop_sequences or []:
        if not s:
            continue
        idx = text.find(s)
        if idx != -1:
            return text[:idx], s  # exclusive
    return text, None


def _truncate_by_max_sentences(text: str, max_sentences: Optional[int]):
    if not max_sentences or max_sentences <= 0:
        return text, False
    endings = list(re.finditer(r"[.!?](?:\s|$)", text))
    if len(endings) <= max_sentences:
        return text, False
    cutoff = endings[max_sentences - 1].end()
    return text[:cutoff].rstrip(), True


# --------------------------------------------------------------------------
# vLLM backend call
# --------------------------------------------------------------------------

def _post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        VLLM_BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
        return json.loads(r.read())


def _generate_one(p: GenerateParams) -> dict:
    enable_thinking = bool(p.enable_thinking) if p.enable_thinking is not None else False
    system = p.system_message or p.system_prompt or DEFAULT_SYSTEM
    max_tokens = p.max_length or 100
    temperature = p.temperature if (p.temperature and p.temperature > 0) else 1.0

    extra = {"top_k": p.top_k if p.top_k is not None else 40,
             "chat_template_kwargs": {"enable_thinking": enable_thinking}}
    if p.repetition_penalty and p.repetition_penalty > 1.0:
        extra["repetition_penalty"] = p.repetition_penalty
    body = {
        "model": VLLM_MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": p.text}],
        # request a little headroom so min_probability/stop can trim down to spec
        "max_tokens": max_tokens + (96 if enable_thinking else 0),
        "temperature": temperature,
        "top_p": p.top_p if p.top_p is not None else 0.9,
        "logprobs": True,
        "top_logprobs": 1,
        **({"seed": p.seed} if p.seed else {}),
        **extra,
    }
    out = _post("/v1/chat/completions", body)
    choice = out["choices"][0]
    full_text = choice["message"]["content"] or ""

    # per-token argmax probs from logprobs.content[*].top_logprobs[0]
    lp = (choice.get("logprobs") or {}).get("content") or []
    token_strs = [c.get("token", "") for c in lp]
    argmax_probs = []
    for c in lp:
        tops = c.get("top_logprobs") or []
        best = tops[0]["logprob"] if tops else c.get("logprob", 0.0)
        argmax_probs.append(math.exp(best))

    thinking_content, response_text = _split_thinking(full_text)
    # align argmax_probs / tokens to the response region (after thinking)
    resp_token_offset = 0
    if thinking_content is not None and token_strs:
        # find where </think> ends in token stream by reconstructing length
        acc = ""
        for i, t in enumerate(token_strs):
            acc += t
            if "</think>" in acc:
                resp_token_offset = i + 1
                break
    resp_probs = argmax_probs[resp_token_offset:]
    resp_tokens = token_strs[resp_token_offset:]

    stop_reason = "stop" if choice.get("finish_reason") in ("stop", None) else "max_length"

    # 1) min_probability (inclusive truncate on response tokens)
    if p.min_probability and p.min_probability > 0 and resp_probs:
        keep, triggered = _truncate_by_min_probability(resp_probs, resp_tokens, p.min_probability)
        if triggered:
            response_text = "".join(resp_tokens[:keep])
            stop_reason = "min_probability"

    # 2) max_length token cap on the response
    if max_tokens and len(resp_tokens) > max_tokens and stop_reason == "stop":
        # only when not already trimmed shorter
        capped = "".join(resp_tokens[:max_tokens]) if resp_tokens else response_text
        if len(capped) < len(response_text):
            response_text = capped
            stop_reason = "max_length"

    # 3) stop_sequences (exclusive); reason becomes the matched sequence
    response_text, matched = _truncate_by_stop_sequences(response_text, p.stop_sequences)
    if matched is not None and stop_reason == "stop":
        stop_reason = matched

    # 4) max_sentences
    response_text, sent_trim = _truncate_by_max_sentences(response_text, p.max_sentences)
    if sent_trim and stop_reason == "stop":
        stop_reason = "max_sentences"

    generated_text = p.text + response_text
    return {"generated_text": generated_text, "stop_reason": stop_reason,
            "thinking_content": thinking_content}


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.post("/api/v1/generate")
def generate(params: GenerateParams, secret: Optional[str] = Header(default=None)):
    if not params.text or not params.text.strip():
        raise HTTPException(status_code=400, detail="Please enter some text")
    _ensure_backend()
    n = max(1, params.number_of_results or 1)
    return [_generate_one(params) for _ in range(n)]


# --------------------------------------------------------------------------
# OpenAI-compatible endpoints (full inference_server parity for the LB)
# --------------------------------------------------------------------------

class OpenaiParams(BaseModel):
    model: Optional[str] = None
    prompt: Optional[str] = None
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    stop: Optional[List[str]] = None
    echo: Optional[bool] = False
    seed: Optional[int] = None
    repetition_penalty: Optional[float] = 1.2


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionParams(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    stop: Optional[List[str]] = None
    seed: Optional[int] = None
    repetition_penalty: Optional[float] = 1.2
    enable_thinking: Optional[bool] = True


@app.post("/v1/completions")
def completions(params: OpenaiParams):
    _ensure_backend()
    gp = GenerateParams(
        text=params.prompt or "", max_length=params.max_tokens or 100,
        temperature=params.temperature, top_p=params.top_p, top_k=params.top_k,
        stop_sequences=params.stop or [], seed=params.seed,
        repetition_penalty=params.repetition_penalty,
    )
    res = _generate_one(gp)
    text = res["generated_text"]
    if not params.echo and text.startswith(gp.text):
        text = text[len(gp.text):]
    return {
        "id": "cmpl-" + _rand_id(), "object": "text_completion",
        "created": int(time.time()), "model": SERVED_NAME,
        "choices": [{"text": text, "index": 0, "logprobs": None,
                     "finish_reason": res["stop_reason"]}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 1, "total_tokens": 1},
    }


@app.post("/v1/chat/completions")
def chat_completions(params: ChatCompletionParams):
    _ensure_backend()
    # forward chat messages straight to the vLLM chat backend
    extra = {"top_k": params.top_k if params.top_k is not None else 40,
             "chat_template_kwargs": {"enable_thinking": bool(params.enable_thinking)}}
    if params.repetition_penalty and params.repetition_penalty > 1.0:
        extra["repetition_penalty"] = params.repetition_penalty
    body = {
        "model": VLLM_MODEL,
        "messages": [m.dict() for m in params.messages],
        "max_tokens": params.max_tokens or 512,
        "temperature": params.temperature if (params.temperature and params.temperature > 0) else 1.0,
        "top_p": params.top_p if params.top_p is not None else 0.9,
        **({"stop": params.stop} if params.stop else {}),
        **({"seed": params.seed} if params.seed else {}),
        **extra,
    }
    out = _post("/v1/chat/completions", body)
    choice = out["choices"][0]
    full = choice["message"]["content"] or ""
    thinking, response = _split_thinking(full)
    message = {"role": "assistant", "content": response}
    if thinking:
        message["reasoning_content"] = thinking
    return {
        "id": "chatcmpl-" + _rand_id(), "object": "chat.completion",
        "created": int(time.time()), "model": SERVED_NAME,
        "choices": [{"index": 0, "message": message,
                     "finish_reason": choice.get("finish_reason") or "stop"}],
        "usage": out.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
    }


@app.get("/liveness_check")
def liveness_check(deep: int = 0):
    # In managed mode an intentionally idle-unloaded backend is HEALTHY, not down:
    # report ok with empty cached_models (mirrors the real server's idle state).
    if BACKEND is not None and not BACKEND.status()["ready"]:
        return {"status": "ok", "inference": "ok", "cached_models": []}
    try:
        with urllib.request.urlopen(VLLM_BASE + "/v1/models", timeout=10) as r:
            models = json.loads(r.read())
        cached = [m.get("id") for m in models.get("data", [])]
        result = {"status": "ok", "inference": "ok", "cached_models": cached}
        if deep:
            _ensure_backend()
            probe = _generate_one(GenerateParams(text="ping", max_length=3, temperature=0))
            result["deep_check"] = "ok" if probe.get("generated_text") else "error"
        return result
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"backend unreachable: {e}")


@app.get("/backend_status")
def backend_status():
    if BACKEND is None:
        return {"managed": False, "backend": VLLM_BASE}
    return BACKEND.status()


@app.get("/")
def root():
    return {"service": "vllm-parity-adapter", "backend": VLLM_BASE, "model": SERVED_NAME}
