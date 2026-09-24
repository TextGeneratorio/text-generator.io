"""GPU TTS sidecar for the CPU-only compat worker (:9083).

The compat worker stays CUDA-free so its CPU Gemma/caption models never touch
the shared 5090. This process owns only Kokoro (torch fp32) and Supertonic
(ONNX CUDA EP), keeps them resident and warm, and returns raw float32 PCM.
The worker falls back to its own CPU engines if this sidecar is down or slow.

Run: CUDA_VISIBLE_DEVICES=0 python -m questions.inference_server.tts_gpu_server
"""
import asyncio
import logging
import os
import time

os.environ.setdefault("SUPERTONIC_ENABLE_CUDA", "1")
os.environ.setdefault("IDLE_UNLOAD_SECONDS", "0")
os.environ.setdefault("MAX_CACHED_MODELS", "0")
os.environ.setdefault("MIN_FREE_VRAM_GB", "0")

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from questions.inference_server import inference_server as srv

logger = logging.getLogger("tts_gpu")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

PORT = int(os.environ.get("TTS_GPU_PORT", "9085"))
CONCURRENCY = max(1, int(os.environ.get("TTS_GPU_CONCURRENCY", "2")))
VRAM_CAP_GB = float(os.environ.get("TTS_GPU_VRAM_CAP_GB", "2.5"))

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
    return JSONResponse({"ok": ok, "ready": _ready, "torch_reserved_gb": round(mem, 3)}, status_code=200 if ok else 503)


@app.post("/synth")
async def synth(p: SynthParams):
    t = time.time()
    async with _sem:
        try:
            rate, audio = await asyncio.to_thread(_synth, p.text, p.voice, p.speed, p.language, p.steps)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        except Exception as exc:
            oom = "out of memory" in str(exc).lower()
            logger.warning("synth failed voice=%s oom=%s: %s", p.voice, oom, exc)
            _free_cuda()
            raise HTTPException(503, "gpu tts failed")
    logger.info("synth voice=%s chars=%d audio=%.1fs took=%.3fs", p.voice, len(p.text), len(audio) / rate, time.time() - t)
    return Response(audio.tobytes(), media_type="application/octet-stream", headers={"X-Sample-Rate": str(rate)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning", access_log=False)
