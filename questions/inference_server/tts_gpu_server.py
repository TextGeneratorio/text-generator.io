"""GPU TTS sidecar for the CPU-only compat worker (:9083).

The compat worker stays CUDA-free so its CPU Gemma/caption models never touch
the shared 5090. This process owns only Kokoro (torch fp32) and Supertonic
(ONNX CUDA EP), keeps them resident and warm, and returns raw float32 PCM.
The worker falls back to its own CPU engines if this sidecar is down or slow.

Run: CUDA_VISIBLE_DEVICES=0 python -m questions.inference_server.tts_gpu_server
"""
import asyncio
import json
import logging
import os
import time
import urllib.request

os.environ.setdefault("SUPERTONIC_ENABLE_CUDA", "1")
os.environ.setdefault("IDLE_UNLOAD_SECONDS", "0")
os.environ.setdefault("MAX_CACHED_MODELS", "0")
os.environ.setdefault("MIN_FREE_VRAM_GB", "0")

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.concurrency import iterate_in_threadpool
from pydantic import BaseModel

from questions.inference_server import inference_server as srv

logger = logging.getLogger("tts_gpu")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

PORT = int(os.environ.get("TTS_GPU_PORT", "9085"))
CONCURRENCY = max(1, int(os.environ.get("TTS_GPU_CONCURRENCY", "2")))
VRAM_CAP_GB = float(os.environ.get("TTS_GPU_VRAM_CAP_GB", "2.5"))
# Box-wide VRAM broker (omniserve-native :8791). On OOM, queue for headroom
# there and retry once instead of failing the request.
BROKER = os.environ.get("TTS_GPU_VRAM_BROKER", "http://127.0.0.1:8791")
BROKER_MB = int(os.environ.get("TTS_GPU_BROKER_MB", "768"))
BROKER_WAIT_MS = int(os.environ.get("TTS_GPU_BROKER_WAIT_MS", "8000"))
_stats = {"oom": 0, "oom_retried_ok": 0, "broker_denied": 0}

app = FastAPI()
_sem = None
_ready = {"kokoro": False, "supertonic": False}


def _torch():
    import torch

    return torch


def _cap_vram():
    torch = _torch()
    if not torch.cuda.is_available():
        return
    import questions.inference_server.kokoro  # noqa: F401  sets cudnn.benchmark at import

    # Every new text length is a new conv shape; autotuning each one costs ~0.6s.
    torch.backends.cudnn.benchmark = False
    total = torch.cuda.get_device_properties(0).total_memory / 2**30
    torch.cuda.set_per_process_memory_fraction(min(1.0, VRAM_CAP_GB / total), 0)


def _patch_supertonic_providers():
    """Give Supertonic's ONNX sessions a bounded CUDA arena (its loader only accepts bare names)."""
    import onnxruntime as ort
    import supertonic.loader as loader

    if "CUDAExecutionProvider" not in ort.get_available_providers():
        return
    limit = int(float(os.environ.get("TTS_GPU_ORT_MEM_GB", "1.0")) * 2**30)
    cuda = ("CUDAExecutionProvider", {"device_id": 0, "gpu_mem_limit": limit, "arena_extend_strategy": "kSameAsRequested", "cudnn_conv_algo_search": os.environ.get("TTS_GPU_ORT_CONV_SEARCH", "HEURISTIC")})

    class _Ort:
        def __getattr__(self, name):
            return getattr(ort, name)

        @staticmethod
        def InferenceSession(path, sess_options=None, providers=None):
            providers = [cuda if p == "CUDAExecutionProvider" else p for p in (providers or [])]
            return ort.InferenceSession(path, sess_options=sess_options, providers=providers)

    loader.ort = _Ort()


def _synth(text, voice, speed, language, steps):
    rate, audio = srv.audio_process(text, voice, speed, language=language, steps=steps)
    return rate, np.asarray(audio, dtype=np.float32).reshape(-1)


def _warmup():
    for name, voice in (("kokoro", "af"), ("supertonic", "M1")):
        try:
            t = time.time()
            _synth("Warm up the voice.", voice, 1.0, "en", srv.SUPERTONIC_DEFAULT_STEPS)
            _synth("Warm up the voice with a slightly longer sentence to cover more shapes.", voice, 1.0, "en", srv.SUPERTONIC_DEFAULT_STEPS)
            _ready[name] = True
            logger.info("warm %s %.2fs", name, time.time() - t)
        except Exception as exc:
            logger.warning("warmup %s failed: %s", name, exc)
            _free_cuda()


def _broker(path, body, timeout):
    req = urllib.request.Request(BROKER + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _synth_after_oom(text, voice, speed, language, steps):
    """Free our cache, queue at the broker for headroom, retry once."""
    _free_cuda()
    lease = None
    if BROKER:
        try:
            lease = _broker("/v1/gpu/lease", {"owner": "tts-gpu", "pid": os.getpid(), "mb": BROKER_MB, "min_mb": BROKER_MB, "tier": "sub", "ttl_s": 60, "wait_ms": BROKER_WAIT_MS}, BROKER_WAIT_MS / 1000 + 5)
        except Exception as exc:
            logger.warning("vram broker unreachable: %s", exc)
        if lease is not None and not lease.get("granted"):
            _stats["broker_denied"] += 1
            raise RuntimeError("out of memory (broker denied after %s ms)" % lease.get("waited_ms"))
    try:
        out = _synth(text, voice, speed, language, steps)
        _stats["oom_retried_ok"] += 1
        return out
    finally:
        if lease and lease.get("lease_id"):
            try:
                _broker("/v1/gpu/release", {"lease_id": lease["lease_id"]}, 3)
            except Exception:
                pass


def _synth_guarded(text, voice, speed, language, steps):
    try:
        return _synth(text, voice, speed, language, steps)
    except Exception as exc:
        if "out of memory" not in str(exc).lower():
            raise
        _stats["oom"] += 1
        logger.warning("synth OOM voice=%s; queueing at vram broker", voice)
        return _synth_after_oom(text, voice, speed, language, steps)


def _free_cuda():
    try:
        _torch().cuda.empty_cache()
    except Exception:
        pass


class SynthParams(BaseModel):
    text: str
    voice: str = "af"
    speed: float = 1.0
    language: str = "en"
    steps: int = 4


@app.on_event("startup")
async def _startup():
    global _sem
    _sem = asyncio.Semaphore(CONCURRENCY)
    _cap_vram()
    _patch_supertonic_providers()
    await asyncio.to_thread(_warmup)


@app.get("/health")
async def health():
    torch = _torch()
    mem = torch.cuda.memory_reserved(0) / 2**30 if torch.cuda.is_available() else 0.0
    ok = any(_ready.values())
    return JSONResponse({"ok": ok, "ready": _ready, "torch_reserved_gb": round(mem, 3), "vram": _stats}, status_code=200 if ok else 503)


@app.post("/synth")
async def synth(p: SynthParams):
    t = time.time()
    async with _sem:
        try:
            rate, audio = await asyncio.to_thread(_synth_guarded, p.text, p.voice, p.speed, p.language, p.steps)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        except Exception as exc:
            oom = "out of memory" in str(exc).lower()
            logger.warning("synth failed voice=%s oom=%s: %s", p.voice, oom, exc)
            _free_cuda()
            raise HTTPException(503, "gpu tts failed")
    logger.info("synth voice=%s chars=%d audio=%.1fs took=%.3fs", p.voice, len(p.text), len(audio) / rate, time.time() - t)
    return Response(audio.tobytes(), media_type="application/octet-stream", headers={"X-Sample-Rate": str(rate)})


def _stream_chunks(p):
    """Sync generator of float32 PCM bytes per segment; OOM before the first chunk falls back to a whole retry."""
    t = time.time()
    n, rate = 0, 24000
    first = None
    it = srv.audio_process_stream(p.text, p.voice, p.speed, language=p.language, steps=p.steps)
    try:
        for rate, audio in it:
            if first is None:
                first = time.time() - t
            n += audio.size
            yield rate, audio.astype(np.float32, copy=False).tobytes()
    except Exception as exc:
        if n or "out of memory" not in str(exc).lower():
            raise
        _stats["oom"] += 1
        logger.warning("stream OOM voice=%s; queueing at vram broker", p.voice)
        rate, audio = _synth_after_oom(p.text, p.voice, p.speed, p.language, p.steps)
        first = time.time() - t
        n = audio.size
        yield rate, audio.tobytes()
    logger.info("stream voice=%s chars=%d audio=%.1fs first=%.3fs took=%.3fs", p.voice, len(p.text), n / rate, first or 0, time.time() - t)


async def _next_chunk(gen):
    # The GPU slot is held per segment, so a long stream never blocks another request's first chunk.
    async with _sem:
        return await gen.__anext__()


@app.post("/synth_stream")
async def synth_stream(p: SynthParams):
    """Chunked float32 PCM; the first chunk (first sentence) is sent as soon as it is synthesized."""
    gen = iterate_in_threadpool(_stream_chunks(p))
    try:
        rate, head = await _next_chunk(gen)
    except StopAsyncIteration:
        raise HTTPException(400, "Speech input could not be tokenized for the selected voice.")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.warning("stream failed voice=%s: %s", p.voice, exc)
        _free_cuda()
        raise HTTPException(503, "gpu tts failed")

    async def body():
        yield head
        while True:
            try:
                _, chunk = await _next_chunk(gen)
            except StopAsyncIteration:
                return
            except Exception as exc:
                logger.warning("stream aborted voice=%s: %s", p.voice, exc)
                _free_cuda()
                raise
            yield chunk

    return StreamingResponse(body(), media_type="application/octet-stream", headers={"X-Sample-Rate": str(rate)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning", access_log=False)
