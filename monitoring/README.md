# Production monitoring

This directory owns active contract checks and the 500/error responder for the text-generator.io cutover.

`service_probe.py` sends a one-token continuation request using the public legacy payload. It also validates the legacy 768-dimensional feature-extraction response and the OpenAI `/v1/embeddings` envelope. Checks run through:

- OmniServe Native on `127.0.0.1:8791`
- the managed inference compatibility API on `127.0.0.1:9083`
- production `/api/v1/generate` and `/api/v1/autocomplete`
- native, compatibility, and production embedding routes
- the RA1 pricing and LoRA-search API with `--profile all`

The core probe also requires `omniserve-native.service` and `text-generator-inference.service` to be active, running, and owned by systemd. It verifies the public `/status` response is the native C contract, tests scalar and batched embeddings, and checks the public speech catalogue.

Run it manually:

```bash
python monitoring/service_probe.py --profile core
python monitoring/service_probe.py --profile all
python monitoring/service_probe.py --profile caption
python monitoring/service_probe.py --profile parity
```

RA1 image generation spends credits and is deliberately opt-in:

```bash
RA1_MONITOR_API_KEY=... python monitoring/service_probe.py --profile all --include-ra1-generation
```

`monitor_500s.py --synthetic-probe` converts failed checks into the same incident queue used for server 500s and frontend errors. The systemd unit runs core checks every 15 minutes and the full parity profile every 10 hours. That profile performs Git-base captioning, CPU CLIP image/text classification, a small local Z-Image generation, an actual CPU BiRefNet cutout, and ASR/3D/training worker contracts, then invokes the on-call Codex agent subject to its cooldown.

No secret is committed or printed. Caption monitoring reads `NETWRCK_IMAGE_CAPTION_SECRET` from `/etc/netwrck-image-caption.env`; `TEXTGEN_MONITOR_SECRET` remains available for other authenticated probes. `RA1_MONITOR_API_KEY` is required for paid RA1 generation.

## Service architecture

`omniserve-native.service` is the C data plane. It embeds llama.cpp for the always-warm Gemma model and uses an epoll reactor, fixed worker pool, priority admission, per-modality permits, prefix-aware KV reuse, native JSON parsing, and resolved-once upstream connection pools. It listens only on loopback port 8791.

Nginx sends `api.text-generator.io` to OmniServe Native on port 8791. Native C serves text generation, streaming chat, completions, summarization, and ModernBERT embeddings directly. It relays TTS, STT, multimodal requests, and provider-routed chat to the managed CPU-only compatibility worker on port 9083. Calls from that worker back to the embedded model carry `X-Omniserve-Internal: local`, preventing a proxy loop. The Python OmniServe scheduler on 8790 remains the image/control-plane hop.

The production Cloudflare inference tunnel also terminates directly on port 8791. Its checked-in Supervisor definition is `monitoring/supervisor/cloudflared.conf`; update it through `supervisorctl reread` and `supervisorctl update`, then verify the public hostname. Nginx provides the same route for local/origin HTTP traffic.

Port 9080 is retired from the routing graph. A stale process may temporarily remain there while another interactive agent owns it, but nginx, OmniServe Native, and systemd configuration must never depend on it.

Gobed is a separate 512-dimensional, CPU-only static-embedding lane. OpenPaths serves it as `openpaths-embed` (aliases `gobed`, `gobed-embed`, and `op-embed`) through its authenticated OpenAI-compatible `/v1/embeddings` route. app-site handles that provider in-process so local calls do not loop back through the public gateway.

RA1 is served by the Netwrck Go API. Pricing/search probes are safe. A generation probe requires a valid dedicated key and must return `success=true` with a non-empty `images` array.

## Deployment and verification

Only managed services may be used. Never start Gunicorn/Uvicorn manually and never use broad process-kill commands.

```bash
sudo -n systemctl restart omniserve-native.service
sudo -n systemctl restart text-generator-inference.service
sudo -n systemctl restart text-generator-500-monitor.service
systemctl status omniserve-native.service text-generator-inference.service text-generator-500-monitor.service --no-pager --lines=30
python monitoring/service_probe.py --profile all
```

After changing C code, build and test `omniserve-native` before restarting it. After changing the compatibility API, run its narrow pytest suite before restarting inference. Always rerun the exact production continuation request and both embedding contracts after deployment. Completion output must preserve the input prefix, start its continuation at a word boundary, and contain non-whitespace text; embedding output must contain the requested number of finite numeric values.
