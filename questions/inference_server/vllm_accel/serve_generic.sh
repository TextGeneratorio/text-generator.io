#!/usr/bin/env bash
set -euo pipefail
VENV=/nvme0n1-disk/code/openpaths/.venv-vllm
MODEL=${MODEL:?set MODEL}
PORT=${PORT:-8200}
export TMPDIR=/nvme0n1-disk/tmp HF_HOME=/nvme0n1-disk/hf_cache
export CUDA_HOME=${CUDA_HOME:-/usr/local/cuda-12.9}
export PATH="$CUDA_HOME/bin:$PATH"
export VLLM_USE_FLASHINFER_SAMPLER=0
export PYTHONPATH="/nvme0n1-disk/tmp/prom_shim${PYTHONPATH:+:$PYTHONPATH}"
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512,expandable_segments:True
ARGS=( -m vllm.entrypoints.openai.api_server --model "$MODEL"
  --served-model-name "${SERVED:-model}" --host 0.0.0.0 --port "$PORT"
  --dtype bfloat16 --max-model-len "${MAXLEN:-4096}"
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION:-0.45}" --max-num-seqs 1
  --trust-remote-code --no-enable-log-requests --disable-uvicorn-access-log )
[[ -n "${SPEC:-}" ]] && ARGS+=( --speculative-config "$SPEC" )
echo "launching: ${ARGS[*]}"
exec "$VENV/bin/python" "${ARGS[@]}"
