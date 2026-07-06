#!/usr/bin/env bash
set -euo pipefail
VENV=/nvme0n1-disk/code/openpaths/.venv-vllm
MODEL=${MODEL:?set MODEL}
PORT=${PORT:-8200}
export TMPDIR=/nvme0n1-disk/tmp HF_HOME=/nvme0n1-disk/hf_cache
export CUDA_HOME=${CUDA_HOME:-/usr/local/cuda-12.9}
export PATH="$CUDA_HOME/bin:$PATH"
export VLLM_USE_FLASHINFER_SAMPLER=0
export PYTHONPATH="/nvme0n1-disk/code/text-generator.io/questions/inference_server/vllm_accel/prom_shim${PYTHONPATH:+:$PYTHONPATH}"
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512,expandable_segments:True
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# Text-only deployment: skip the mm encoder memory profiling AND the
# APIServer renderer's ~40s multimodal warmup (via the wrapper entrypoint).
# NOTE: --limit-mm-per-prompt '{"image":0,"video":0}' would be the supported
# route but crashes Qwen3.5 engine init on vLLM 0.22.1 (NoneType.size in the
# compiled text-only forward), hence the wrapper.
ENTRY=( -m vllm.entrypoints.openai.api_server )
[[ "${TEXT_ONLY:-1}" == "1" ]] && ENTRY=( "$SCRIPT_DIR/serve_textonly_entry.py" )
ARGS=( "${ENTRY[@]}" --model "$MODEL"
  --served-model-name "${SERVED:-model}" --host 0.0.0.0 --port "$PORT"
  --dtype bfloat16 --max-model-len "${MAXLEN:-4096}"
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION:-0.45}"
  --max-num-seqs "${MAX_NUM_SEQS:-8}"
  --trust-remote-code --no-enable-log-requests --disable-uvicorn-access-log )
[[ "${PREFIX_CACHE:-1}" == "1" ]] && ARGS+=( --enable-prefix-caching )
# Sleep mode routes allocations through CuMemAllocator so /sleep level 1 can
# actually release VRAM (weights -> pinned CPU RAM, KV dropped). Paired with
# VLLM_SERVER_DEV_MODE=1 (set by vllm_backend_manager) for the /sleep routes.
[[ "${SLEEP_MODE:-1}" == "1" ]] && ARGS+=( --enable-sleep-mode )
[[ "${TEXT_ONLY:-1}" == "1" ]] && ARGS+=( --skip-mm-profiling )
[[ -n "${SPEC:-}" ]] && ARGS+=( --speculative-config "$SPEC" )
ARGS+=( "$@" )
echo "launching: ${ARGS[*]}"
exec "$VENV/bin/python" "${ARGS[@]}"
