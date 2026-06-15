#!/usr/bin/env bash
set -euo pipefail

echo "WARNING: Run tests + pip install before deploying"

# Sync static files to Cloudflare R2 bucket
aws s3 sync ./static s3://text-generatorstatic/static \
  --endpoint-url https://f76d25b8b86cfa5638f43016510d8f77.r2.cloudflarestorage.com
