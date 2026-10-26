#!/usr/bin/env bash
# usage: ./deploy.sh            sync static to R2, then purge the Cloudflare cache
#        ./deploy.sh --purge    purge the Cloudflare cache only
set -euo pipefail

ZONE_NAME="${CF_ZONE_NAME:-text-generator.io}"

purge_cache() {
  : "${CLOUDFLARE_EMAIL:?set CLOUDFLARE_EMAIL}" "${CLOUDFLARE_API_KEY:?set CLOUDFLARE_API_KEY}"
  local api=https://api.cloudflare.com/client/v4
  local auth=(-H "X-Auth-Email: $CLOUDFLARE_EMAIL" -H "X-Auth-Key: $CLOUDFLARE_API_KEY")
  local zone
  zone=$(curl -fsS "${auth[@]}" "$api/zones?name=$ZONE_NAME" | python3 -c 'import json,sys; r=json.load(sys.stdin)["result"]; print(r[0]["id"] if r else "")')
  [ -n "$zone" ] || { echo "zone $ZONE_NAME not found" >&2; exit 1; }
  curl -fsS -X POST "${auth[@]}" -H "Content-Type: application/json" \
    --data '{"purge_everything":true}' "$api/zones/$zone/purge_cache" | python3 -c 'import json,sys; r=json.load(sys.stdin); print("cloudflare purge:", "ok" if r["success"] else r["errors"]); sys.exit(0 if r["success"] else 1)'
}

if [ "${1:-}" != "--purge" ]; then
  echo "WARNING: Run tests + pip install before deploying"
  aws s3 sync ./static s3://text-generatorstatic/static \
    --endpoint-url https://f76d25b8b86cfa5638f43016510d8f77.r2.cloudflarestorage.com
fi

purge_cache
