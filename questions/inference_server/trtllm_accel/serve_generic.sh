#!/usr/bin/env bash
# TensorRT-LLM PyTorch-backend launcher for the existing parity adapter.
#
# The backend manager deliberately keeps its historical VLLM_* environment
# names so this launcher can be swapped into the same lazy-start path without
# changing the public text-generator.io contract.  Set VLLM_SLEEP_MODE=0 when
# using it: TensorRT-LLM does not implement vLLM's /sleep and /wake_up API.
set -euo pipefail

VENV=${TRTLLM_VENV:-/nvme0n1-disk/code/omniserve-native/.venv-trtllm}
MODEL=${MODEL:?set MODEL to a Hugging Face model directory or model id}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8200}
export TMPDIR=${TMPDIR:-/nvme0n1-disk/tmp}
export HF_HOME=${HF_HOME:-/nvme0n1-disk/hf_cache}
export CUDA_HOME=${CUDA_HOME:-/usr/local/cuda-12.9}
export PATH="$CUDA_HOME/bin:$VENV/bin:$PATH"
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}

# Pip installs the CUDA 13 libraries under the venv rather than registering
# them with ldconfig. Put the CUDA 13 cublas directory first: TensorRT-LLM's
# bindings require libcublasLt.so.13 even on a host whose toolkit is 12.9.
site_packages=$(echo "$VENV"/lib/python*/site-packages)
library_path="$site_packages/nvidia/cublas/lib:$site_packages/nvidia/cu13/lib"
for library_dir in "$site_packages"/nvidia/*/lib; do
  [[ -d "$library_dir" ]] && library_path="$library_path:$library_dir"
done
export LD_LIBRARY_PATH="$library_path${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

TRTLLM_SERVE=${TRTLLM_SERVE:-$VENV/bin/trtllm-serve}
if [[ ! -x "$TRTLLM_SERVE" ]]; then
  echo "TensorRT-LLM launcher not found or not executable: $TRTLLM_SERVE" >&2
  echo "Install tensorrt_llm into TRTLLM_VENV or set TRTLLM_SERVE explicitly." >&2
  exit 127
fi

# TensorRT-LLM 1.2 uses the explicit `serve` subcommand and the PyTorch backend;
# no legacy engine-build step is needed.  Keep optional capacity flags out of
# the default command so the same script can be used for a small smoke model
# and the larger Gemma4 checkpoint.
ARGS=("$TRTLLM_SERVE" serve "$MODEL"
  --backend pytorch
  --host "$HOST"
  --port "$PORT"
)
[[ -n "${TP_SIZE:-}" ]] && ARGS+=(--tp_size "$TP_SIZE")
[[ -n "${PP_SIZE:-}" ]] && ARGS+=(--pp_size "$PP_SIZE")
[[ -n "${MAX_SEQ_LEN:-}" ]] && ARGS+=(--max_seq_len "$MAX_SEQ_LEN")
[[ -n "${MAX_BATCH_SIZE:-}" ]] && ARGS+=(--max_batch_size "$MAX_BATCH_SIZE")
[[ -n "${MAX_NUM_TOKENS:-}" ]] && ARGS+=(--max_num_tokens "$MAX_NUM_TOKENS")
[[ -n "${KV_CACHE_FREE_GPU_MEMORY_FRACTION:-}" ]] && \
  ARGS+=(--kv_cache_free_gpu_memory_fraction "$KV_CACHE_FREE_GPU_MEMORY_FRACTION")
[[ "${TRUST_REMOTE_CODE:-1}" == "1" ]] && ARGS+=(--trust_remote_code)
ARGS+=("$@")

echo "launching: ${ARGS[*]}"
exec "${ARGS[@]}"
