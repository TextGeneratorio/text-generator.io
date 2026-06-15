#!/usr/bin/env bash
# Launch the baked Gemma-4 E4B on vLLM on the 5090.
# Usage: ./serve_5090.sh [spec]   ('spec' adds the MTP drafter)
set -euo pipefail

VENV=/nvme0n1-disk/code/openpaths/.venv-vllm
MODEL=/nvme0n1-disk/code/openpaths/local/weights/osoi-rm35-baked
DRAFTER=/nvme0n1-disk/code/openpaths/local/weights/drafter-ft/epoch_002-final
PORT=${PORT:-8000}

export TMPDIR=/nvme0n1-disk/tmp
export HF_HOME=/nvme0n1-disk/hf_cache
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512,expandable_segments:True
export VLLM_LOGGING_LEVEL=INFO

# FlashInfer JIT-compiles sampling kernels at startup; point it at a real nvcc
# (driver-derived /usr/local/cuda-12.0 has none) and avoid the JIT sampler path.
export CUDA_HOME=${CUDA_HOME:-/usr/local/cuda-12.9}
export PATH="$CUDA_HOME/bin:$PATH"
export VLLM_USE_FLASHINFER_SAMPLER=0

# PCK04: scatter the pruned 16k lm_head back to full 262144 vocab (accuracy-faithful).
# Required because the baked weights ship a pruned/int4 lm_head.
SUB=/nvme0n1-disk/code/openpaths/local/submissions/frantic-penguin/osoi5-feopt2-w20-e1-lmhead12k-fa2sw-precache-skv64-fp-v1
if [[ "${OPT:-0}" == "1" ]]; then
  # Honest optimization stack: pck04 + onegraph drafter CUDA-graph loop + fused
  # sparse argmax + FA2 sliding-window + split-KV verify. No precache (cheat).
  export OPT_SUB_DIR="$SUB"
  export PYTHONPATH="/nvme0n1-disk/tmp/opt_shim:$SUB${PYTHONPATH:+:$PYTHONPATH}"
  export PCK04_KEEPSET="$MODEL/pck04_keepset.json"
  export ONEGRAPH=1 FUSED_SPARSE_ARGMAX=1 FUSED_SPARSE_ARGMAX_BLOCK=64
  export LOOPGRAPH_PINGPONG_SLOTS=${LOOPGRAPH_PINGPONG_SLOTS:-3} LOOPGRAPH_WARMUP_CALLS=${LOOPGRAPH_WARMUP_CALLS:-20}
  export DIXIE_FUSED_ACCEPT_PREP=1
  export FA_SLIDING=${FA_SLIDING:-1}
  export SPLITKV_VERIFY=${SPLITKV_VERIFY:-1} SPLITKV_VERIFY_MAX_Q=64
elif [[ "${PCK04:-1}" == "1" ]]; then
  export PYTHONPATH="/nvme0n1-disk/tmp/pck04_only:$SUB${PYTHONPATH:+:$PYTHONPATH}"
  export PCK04_KEEPSET="$MODEL/pck04_keepset.json"
fi

ARGS=(
  -m vllm.entrypoints.openai.api_server
  --model "$MODEL"
  --served-model-name gemma-4-e4b-it
  --host 0.0.0.0 --port "$PORT"
  --dtype bfloat16
  --max-model-len 4096
  --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION:-0.60}
  --max-num-seqs 1
  --trust-remote-code
  --no-enable-log-requests
  --disable-uvicorn-access-log
)

if [[ "${1:-}" == "spec" ]]; then
  ARGS+=( --speculative-config "{\"method\":\"mtp\",\"model\":\"$DRAFTER\",\"num_speculative_tokens\":7}" )
fi

echo "launching: ${ARGS[*]}"
exec "$VENV/bin/python" "${ARGS[@]}"
