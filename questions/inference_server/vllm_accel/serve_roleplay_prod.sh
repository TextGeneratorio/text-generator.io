#!/usr/bin/env bash
# Production serving config for gemma-roleplay-v2: sweep winner 2026-07-15
# (fp8 weights + MTP-2 spec decode + fp8 KV + async scheduling).
# Sweep: llmtraining/runs/vllm-5090-sweep/summary.json — 264 tok/s single-stream
# (2.0x bf16, 1.6x fp8-only), rubric retention 1.0, adult vocab 3/3.
set -euo pipefail
cd "$(dirname "$0")"
# Cold boot needs ~14GiB contiguous. The image endpoint returns 200 even when
# an in-flight generation keeps Z-Image pinned, so verify that residency is
# actually empty before starting vLLM. The manager performs the same handshake;
# this keeps direct/manual launches safe too.
IMAGE_UNLOAD_URL=${IMAGE_SERVER_UNLOAD_URL:-http://127.0.0.1:8100/admin/unload}
if [[ -n "$IMAGE_UNLOAD_URL" ]]; then
  clear_deadline=${COEXISTING_CLEAR_ATTEMPTS:-30}
  for ((clear_attempt = 1; clear_attempt <= clear_deadline; clear_attempt++)); do
    clear_state=$(curl -sf -X POST --max-time 10 "$IMAGE_UNLOAD_URL" 2>/dev/null || true)
    if [[ -z "$clear_state" ]] || grep -Eq '"loaded"[[:space:]]*:[[:space:]]*\[[[:space:]]*\]' <<<"$clear_state"; then
      break
    fi
    if ((clear_attempt == clear_deadline)); then
      echo "image backend remained resident; refusing an unsafe vLLM cold start" >&2
      exit 75
    fi
    sleep 1
  done
fi
DRAFTER=${DRAFTER:-/nvme0n1-disk/hf_cache/models--google--gemma-4-E4B-it-assistant/snapshots/a9570954c167c2b4e8f9c155ef2ab068cd9d1e26}
export MODEL=${MODEL:-/nvme0n1-disk/code/text-generator.io/llmtraining/models/gemma-roleplay-v2-merged}
export SERVED=${SERVED:-gemma-roleplay-v2}
export PORT=${PORT:-8200}
# 0.40 fits worst-case coexistence: image server (12-16GB elastic, live paid
# traffic reloads it right after any /admin/unload) + this + ~3.4GB of newer
# small GPU procs (cutedsl 0.9, askfelix 0.7, netwrck 1.8). Those small procs
# arrived after the old 0.44 was chosen and ate the headroom, so cold boot
# began OOMing whenever zimage was resident (2026-07-18). 0.40*32.6=13.0GB:
# 15.4+13.0+3.4=31.8 < 32.6. The real fix is omniserve owning the whole card.
export GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.38}
# EAGER=1 disables CUDA graphs; never use with SPEC (drafter loop needs graphs:
# measured 15 tok/s eager vs 261 with graphs)
EAGER=${EAGER:-0}
EXTRA=()
[[ "$EAGER" == "1" ]] && EXTRA+=( --enforce-eager )
export MAXLEN=${MAXLEN:-4096}
export MAX_NUM_SEQS=${MAX_NUM_SEQS:-4}
export QUANT=fp8
export KV_CACHE_DTYPE=fp8
export ASYNC_SCHEDULING=1
export SPEC=$(printf '{"method":"mtp","model":"%s","num_speculative_tokens":%s}' "$DRAFTER" "${NUM_SPEC:-2}")
# 768MiB fp8 KV still holds roughly 9 simultaneous 4k contexts, over twice
# MAX_NUM_SEQS=4, while preserving ~280MiB more startup headroom than the old
# 1.1GB reservation. That headroom prevents the final KV allocation OOM seen
# after weights and CUDA graphs had already loaded.
# combo-kernel autotune allocates ~5GB during compile; disabled so cold boots
# fit beside the image server (12-16GB elastic)
exec ./serve_generic.sh --kv-cache-memory-bytes "${KV_BYTES:-805306368}" \
  --compilation-config '{"inductor_compile_config":{"combo_kernels":false,"benchmark_combo_kernel":false}}' \
  "${EXTRA[@]}"
