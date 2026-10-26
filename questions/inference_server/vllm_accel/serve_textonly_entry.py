"""vLLM OpenAI server entry wrapper for text-only deployments.

Skips the APIServer renderer's multi-modal processor warmup (~40s on boot for
multimodal-capable models like Qwen3.5 even when only text is ever served).
Everything else (chat-template warmup, engine init) is untouched. Used by
serve_generic.sh when TEXT_ONLY=1.

The __main__ guard is required: vLLM spawns EngineCore workers with the
multiprocessing "spawn" method, which re-imports this main module.
"""
import runpy

import vllm.renderers.base as _rb


def _skip_mm_warmup(self, processor, *, log_prefix=""):
    return None


_rb.BaseRenderer._warmup_mm_processor = _skip_mm_warmup

if __name__ == "__main__":
    runpy.run_module("vllm.entrypoints.openai.api_server", run_name="__main__")
