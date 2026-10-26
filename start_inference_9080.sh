#!/bin/bash
# Inference server (:9080). CUDA_VISIBLE_DEVICES must stay empty: text gen
# proxies to the vLLM adapter (:8300); if this worker can see the GPU it loads
# ~9GB of aux models and the roleplay backend can never boot (2026-07-18 outage).
set -euo pipefail
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES=""
export VLLM_ADAPTER_BASE="${VLLM_ADAPTER_BASE:-http://127.0.0.1:8300}"
export PRELOAD_MODELS=0 KEEP_ALL_ON_GPU=0 MAX_CACHED_MODELS=3 MIN_FREE_VRAM_GB=4.0
export PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1
# STT is served by Gemini (drops local Parakeet + Gemma-audio, which can't run
# on this CPU-pinned server). The env GEMINI_API_KEY is stale/invalid, so source
# the working key from openpaths without hardcoding a secret here.
export STT_BACKEND="${STT_BACKEND:-gemini}"
if [[ -z "${GEMINI_STT_API_KEY:-}" && -f /nvme0n1-disk/code/openpaths/.env ]]; then
  export GEMINI_STT_API_KEY="$(grep -m1 '^GEMINI_API_KEY=' /nvme0n1-disk/code/openpaths/.env | cut -d= -f2- | tr -d '"')"
fi
exec .venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -b :9080 \
  questions.inference_server.inference_server:app \
  --timeout 1800 --graceful-timeout 120 --workers 1 \
  --max-requests 1000 --max-requests-jitter 200
