#!/usr/bin/env python
"""
Quick profiler for inference - single run analysis.
"""

import cProfile
import gc
import io
import pstats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch


def profile_single_run():
    """Profile a single inference run."""
    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import fast_inference

    model_cache = ModelCache()
    params = GenerateParams(
        text="Once upon a time",
        max_length=20,  # Short generation for profiling
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        number_of_results=1,
        model="any",
    )

    # Single warmup
    print("Warmup...")
    fast_inference(params, model_cache)
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Profile single run
    print("Profiling single inference run...")
    profiler = cProfile.Profile()
    profiler.enable()

    result = fast_inference(params, model_cache)

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    profiler.disable()

    # Print stats
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("cumulative")

    print("\n" + "="*60)
    print("TOP 25 FUNCTIONS BY CUMULATIVE TIME")
    print("="*60 + "\n")

    stats.print_stats(25)
    print(stream.getvalue())

    # Component analysis
    print("\n" + "="*60)
    print("TIME BY COMPONENT")
    print("="*60)

    component_times = {
        "torch": 0.0,
        "transformers": 0.0,
        "tokenizers": 0.0,
        "custom": 0.0,
        "other": 0.0,
    }

    for func, (cc, nc, tt, ct, callers) in profiler.stats.items():
        filename = str(func[0])
        funcname = str(func[2])

        if "torch" in filename.lower():
            component_times["torch"] += ct
        elif "transformers" in filename.lower():
            component_times["transformers"] += ct
        elif "tokenizers" in filename.lower():
            component_times["tokenizers"] += ct
        elif "questions/" in filename or "test" in filename:
            component_times["custom"] += ct
        else:
            component_times["other"] += ct

    total = sum(component_times.values())
    if total > 0:
        for comp, time in sorted(component_times.items(), key=lambda x: -x[1]):
            pct = (time / total) * 100
            print(f"  {comp:<15} {time:>8.3f}s ({pct:>5.1f}%)")

    return result


if __name__ == "__main__":
    profile_single_run()
