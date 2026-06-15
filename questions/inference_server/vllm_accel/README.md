# vLLM acceleration + inference_server API parity

A fast vLLM-backed serving path that speaks the existing `inference_server`
HTTP contract, so the load balancer can route to it as a first-class backend
while it runs at much higher tok/s than the HF-transformers path.

## Components

- **`../vllm_parity_adapter.py`** — FastAPI app exposing the inference_server API
  over a vLLM OpenAI backend:
  - `POST /api/v1/generate` with exact `GenerateParams` semantics
    (`min_probability` via logprobs, `max_sentences`, `stop_sequences` exclusive,
    `max_length` cap, `stop_reason` precedence, `number_of_results`, `<think>`
    split → `thinking_content`, `generated_text` = prompt + continuation).
  - `POST /v1/completions`, `POST /v1/chat/completions` (OpenAI shape;
    `reasoning_content` for thinking; prompt-strip on `echo=false`).
  - `GET /liveness_check`, `GET /backend_status`.
- **`../vllm_backend_manager.py`** — on-demand GPU lifecycle: lazy-start the vLLM
  backend on first request, idle-unload after `IDLE_UNLOAD_SECONDS` of no traffic
  to free VRAM (kills the whole process group so the vLLM EngineCore child also
  dies — a plain SIGTERM leaks the worker's VRAM). Mirrors `model_cache.py`.
- **`serve_5090.sh`** — launches the baked Gemma-4 E4B on vLLM (machine-specific
  weight paths; `spec` arg adds the MTP drafter, `OPT=1` adds the honest
  onegraph/fa2sw/split-KV stack). Reference for the backend command.
- **`bench_tps.py`** — single-stream decode TPS benchmark.
- **`parity_test.py`** — schema + per-param parity checks vs the real server.

## Measured on RTX 5090 (greedy, full accuracy)

| Path | tok/s |
|------|------:|
| HF `transformers.generate()` (current prod) | ~12 |
| vLLM baseline, no spec | 267 |
| vLLM + MTP speculative (K=7) | 390–460 |
| + onegraph/fa2sw/split-KV (`OPT=1`) | ~330–1200 (typ. 700–1000) |

(For reference, the A10G challenge frontier was 489 tok/s with the full stack.)

## Run

Proxy a running backend:
```bash
VLLM_BASE=http://127.0.0.1:8200 VLLM_MODEL=gemma-4-e4b-it \
  uvicorn questions.inference_server.vllm_parity_adapter:app --port 8300
```

Managed (lazy-start + idle-unload) — set `VLLM_BACKEND_CMD`:
```bash
VLLM_BASE=http://127.0.0.1:8200 VLLM_MODEL=gemma-4-e4b-it \
VLLM_BACKEND_CMD='OPT=1 ./serve_5090.sh spec' \
VLLM_BACKEND_CWD=/path/to/serve/dir VLLM_BACKEND_PORT=8200 \
IDLE_UNLOAD_SECONDS=600 \
  uvicorn questions.inference_server.vllm_parity_adapter:app --port 8300
```

## Notes / gotchas

- The vLLM venv + weights live outside the repo (machine-specific, large).
- Gemma weights ship a pruned/int4 lm_head → needs the PCK04 scatter patch
  (full-accuracy) referenced by `serve_5090.sh`.
- FlashInfer JITs a sampler kernel at startup against a stale CUDA path — set
  `CUDA_HOME` to a real toolkit and `VLLM_USE_FLASHINFER_SAMPLER=0`.
- Kill backends by process group / `fuser -k <port>/tcp`; the EngineCore child
  must be killed too or it leaks VRAM (the manager handles this).
