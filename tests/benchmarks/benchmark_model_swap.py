#!/usr/bin/env python
"""
Benchmark model swap behavior without running the server.

This separates the phases that matter for production latency:
- cold_request: first request in a fresh process
- warm_request: cache hit while the model is already GPU-resident
- cpu_offload: current idle-unload behavior, moving cached models off GPU
- restore_request: next request after CPU offload, moving the model back to GPU

Example:
  PATH=.venv/bin:$PATH PYTHONPATH=. python tests/benchmarks/benchmark_model_swap.py --cycles 2 --max-length 8
"""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR))

import torch


@dataclass
class PhaseResult:
    cycle: int
    phase: str
    seconds: float
    gpu_before_gb: dict[str, float]
    gpu_after_gb: dict[str, float]
    cached_models: list[str]
    output_preview: str | None = None


def cuda_sync() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def gpu_memory_gb() -> dict[str, float]:
    if not torch.cuda.is_available():
        return {"allocated": 0.0, "reserved": 0.0, "total": 0.0, "free_driver": 0.0}

    free_bytes, total_bytes = torch.cuda.mem_get_info()
    return {
        "allocated": round(torch.cuda.memory_allocated() / (1024**3), 3),
        "reserved": round(torch.cuda.memory_reserved() / (1024**3), 3),
        "total": round(total_bytes / (1024**3), 3),
        "free_driver": round(free_bytes / (1024**3), 3),
    }


def timed_phase(
    cycle: int,
    phase: str,
    cache: Any,
    func: Callable[[], Any],
) -> PhaseResult:
    gc.collect()
    cuda_sync()
    before = gpu_memory_gb()
    start = time.perf_counter()
    result = func()
    cuda_sync()
    seconds = time.perf_counter() - start
    after = gpu_memory_gb()

    output_preview = None
    if isinstance(result, list) and result and isinstance(result[0], dict):
        generated = result[0].get("generated_text")
        if isinstance(generated, str):
            output_preview = generated[:120]

    return PhaseResult(
        cycle=cycle,
        phase=phase,
        seconds=seconds,
        gpu_before_gb=before,
        gpu_after_gb=after,
        cached_models=cache.list_models(),
        output_preview=output_preview,
    )


def summarize(results: list[PhaseResult]) -> dict[str, dict[str, float]]:
    by_phase: dict[str, list[float]] = {}
    for result in results:
        by_phase.setdefault(result.phase, []).append(result.seconds)

    summary = {}
    for phase, values in by_phase.items():
        summary[phase] = {
            "count": len(values),
            "mean_s": round(statistics.mean(values), 4),
            "min_s": round(min(values), 4),
            "max_s": round(max(values), 4),
        }
        if len(values) > 1:
            summary[phase]["stdev_s"] = round(statistics.stdev(values), 4)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Text Generator model swap latency.")
    parser.add_argument("--cycles", type=int, default=2, help="Number of offload/restore cycles to run.")
    parser.add_argument("--warm-runs", type=int, default=2, help="Warm cache-hit requests per cycle.")
    parser.add_argument("--text", default="The quick brown fox jumps over", help="Prompt text.")
    parser.add_argument("--model", default="any", help="GenerateParams model value.")
    parser.add_argument("--max-length", type=int, default=8, help="Generated token budget.")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import fast_inference

    cache = ModelCache()
    params = GenerateParams(
        text=args.text,
        max_length=args.max_length,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        number_of_results=1,
        model=args.model,
    )

    results: list[PhaseResult] = []

    print("Running model swap benchmark")
    print(f"CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Initial memory: {gpu_memory_gb()}")

    results.append(timed_phase(0, "cold_request", cache, lambda: fast_inference(params, cache)))
    print(f"cold_request: {results[-1].seconds:.3f}s memory={results[-1].gpu_after_gb}")

    for i in range(args.warm_runs):
        phase = f"warm_request_{i + 1}"
        results.append(timed_phase(0, phase, cache, lambda: fast_inference(params, cache)))
        print(f"{phase}: {results[-1].seconds:.3f}s")

    for cycle in range(1, args.cycles + 1):
        results.append(timed_phase(cycle, "cpu_offload", cache, cache.empty_all_caches))
        print(f"cycle {cycle} cpu_offload: {results[-1].seconds:.3f}s memory={results[-1].gpu_after_gb}")

        results.append(timed_phase(cycle, "restore_request", cache, lambda: fast_inference(params, cache)))
        print(f"cycle {cycle} restore_request: {results[-1].seconds:.3f}s memory={results[-1].gpu_after_gb}")

        for i in range(args.warm_runs):
            phase = f"post_restore_warm_{i + 1}"
            results.append(timed_phase(cycle, phase, cache, lambda: fast_inference(params, cache)))
            print(f"cycle {cycle} {phase}: {results[-1].seconds:.3f}s")

    payload = {
        "summary": summarize(results),
        "results": [asdict(result) for result in results],
    }

    print("\nSummary:")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
