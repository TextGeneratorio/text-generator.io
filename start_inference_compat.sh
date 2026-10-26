#!/usr/bin/env bash
# Managed CPU-only compatibility worker behind omniserve-native. The C gateway
# owns the public hot path; this process supplies TTS, STT, multimodal, and
# provider-routing APIs that do not yet have embedded C implementations.
set -euo pipefail

cd "$(dirname "$0")"

export CUDA_VISIBLE_DEVICES=""
export VLLM_TEXT_BACKEND_BASE="${VLLM_TEXT_BACKEND_BASE:-http://127.0.0.1:8791}"
export PRELOAD_MODELS="${PRELOAD_MODELS:-0}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
export STT_BACKEND="${STT_BACKEND:-gemini}"

# Keep the working STT credential outside the repository and process command
# line. openpaths owns the host's current Gemini credential.
if [[ -z "${GEMINI_STT_API_KEY:-}" && -f /nvme0n1-disk/code/openpaths/.env ]]; then
  export GEMINI_STT_API_KEY
  GEMINI_STT_API_KEY=$(sed -n 's/^GEMINI_API_KEY=//p' /nvme0n1-disk/code/openpaths/.env | tail -n 1)
  # dotenv commonly quotes values; query-string credentials must not retain
  # those delimiters or the upstream sees a different key.
  GEMINI_STT_API_KEY=${GEMINI_STT_API_KEY#\"}
  GEMINI_STT_API_KEY=${GEMINI_STT_API_KEY%\"}
  GEMINI_STT_API_KEY=${GEMINI_STT_API_KEY#\'}
  GEMINI_STT_API_KEY=${GEMINI_STT_API_KEY%\'}
fi

# Partner credential shared with the cutedsl image worker. The host credential
# file is the source of truth; scraping the systemd unit only ever returned the
# literal "${CAPTION_BACKEND_API_KEY}" placeholder, which silently 401'd every
# proxied TTS/STT/caption call (2026-07-31).
partner_env_file="${NETWRCK_PARTNER_ENV_FILE:-/etc/netwrck-image-caption.env}"
if [[ -r "$partner_env_file" ]]; then
  while IFS='=' read -r key value; do
    case "$key" in
      NETWRCK_PARTNER_SECRET | NETWRCK_IMAGE_CAPTION_SECRET) ;;
      *) continue ;;
    esac
    value=${value%\"}
    value=${value#\"}
    # An unexpanded ${...} placeholder is worse than nothing: it authenticates
    # nothing and hides the misconfiguration behind a generic 401.
    [[ -z "$value" || "$value" == *'${'* ]] && continue
    printf -v "$key" '%s' "$value"
    export "${key?}"
  done < "$partner_env_file"
fi
export NETWRCK_PARTNER_SECRET="${NETWRCK_PARTNER_SECRET:-${NETWRCK_IMAGE_CAPTION_SECRET:-}}"
if [[ -z "${NETWRCK_PARTNER_SECRET}" ]]; then
  echo "WARNING: no partner secret in $partner_env_file — proxied TTS/STT/caption will 401" >&2
fi
unset partner_env_file

compat_port="${TEXTGEN_COMPAT_PORT:-9083}"
exec .venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -b "127.0.0.1:${compat_port}" \
  questions.inference_server.inference_server:app \
  --timeout 1800 --graceful-timeout 120 --workers 1 \
  --max-requests 1000 --max-requests-jitter 200
