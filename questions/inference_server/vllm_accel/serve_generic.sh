#!/usr/bin/env bash
set -euo pipefail
VENV=${VLLM_VENV:-/nvme0n1-disk/code/openpaths/.venv-vllm-025}
MODEL=${MODEL:?set MODEL}
PORT=${PORT:-8200}
export TMPDIR=/nvme0n1-disk/tmp HF_HOME=/nvme0n1-disk/hf_cache
export CUDA_HOME=${CUDA_HOME:-/usr/local/cuda-12.9}
export PATH="$CUDA_HOME/bin:$PATH"
export VLLM_USE_FLASHINFER_SAMPLER=0
export PYTHONPATH="/nvme0n1-disk/code/text-generator.io/questions/inference_server/vllm_accel/prom_shim${PYTHONPATH:+:$PYTHONPATH}"
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512,expandable_segments:True
# vLLM 0.25 removed the legacy api_server module. Its supported CLI also has
# --language-model-only, so text deployments no longer need the renderer
# monkeypatch in serve_textonly_entry.py. Set VLLM_LEGACY_ENTRYPOINT=1 only to
# roll back to the old 0.22 environment while comparing performance.
if [[ "${VLLM_LEGACY_ENTRYPOINT:-0}" == "1" ]]; then
  SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
  ENTRY=( "$VENV/bin/python" -m vllm.entrypoints.openai.api_server --model "$MODEL" )
  [[ "${TEXT_ONLY:-1}" == "1" ]] && ENTRY=( "$VENV/bin/python" "$SCRIPT_DIR/serve_textonly_entry.py" --model "$MODEL" )
else
  ENTRY=( "$VENV/bin/vllm" serve "$MODEL" )
fi
ARGS=( "${ENTRY[@]}"
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
if [[ "${TEXT_ONLY:-1}" == "1" ]]; then
  [[ "${VLLM_LEGACY_ENTRYPOINT:-0}" != "1" ]] && ARGS+=( --language-model-only )
  ARGS+=( --skip-mm-profiling )
fi
[[ -n "${QUANT:-}" ]] && ARGS+=( --quantization "$QUANT" )
[[ -n "${SPEC:-}" ]] && ARGS+=( --speculative-config "$SPEC" )
[[ -n "${KV_CACHE_DTYPE:-}" ]] && ARGS+=( --kv-cache-dtype "$KV_CACHE_DTYPE" )
[[ -n "${MAX_NUM_BATCHED_TOKENS:-}" ]] && ARGS+=( --max-num-batched-tokens "$MAX_NUM_BATCHED_TOKENS" )
[[ "${ASYNC_SCHEDULING:-0}" == "1" ]] && ARGS+=( --async-scheduling )
ARGS+=( "$@" )
echo "launching: ${ARGS[*]}"
exec "${ARGS[@]}"
