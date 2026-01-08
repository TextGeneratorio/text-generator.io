#!/usr/bin/env python
"""Test the new optimization features."""

import gc
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch


def benchmark(fn, name, num_runs=5):
    """Quick benchmark."""
    times = []
    for i in range(num_runs):
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        start = time.perf_counter()

        result = fn()

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        print(f"  {name} run {i+1}: {elapsed:.1f}ms")

    return {
        "name": name,
        "mean": statistics.mean(times),
        "std": statistics.stdev(times) if len(times) > 1 else 0,
    }


def main():
    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import direct_inference

    print("="*60)
    print("OPTIMIZATION TESTS")
    print("="*60)

    model_cache = ModelCache()

    params = GenerateParams(
        text="The quick brown fox",
        max_length=30,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        number_of_results=1,
        model="any",
    )

    # Warmup - first use fast_inference to load the model
    print("\nWarmup (loading model via fast_inference)...")
    from questions.text_generator_inference import fast_inference
    fast_inference(params, model_cache)

    print("Warmup direct_inference...")
    direct_inference(params, model_cache, use_static_cache=False)

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    results = []

    # Test without static cache
    print("\n--- Without Static Cache ---")
    r1 = benchmark(
        lambda: direct_inference(params, model_cache, use_static_cache=False),
        "dynamic_cache",
        num_runs=5
    )
    results.append(r1)

    # Test with static cache
    print("\n--- With Static Cache ---")
    r2 = benchmark(
        lambda: direct_inference(params, model_cache, use_static_cache=True),
        "static_cache",
        num_runs=5
    )
    results.append(r2)

    # Test tokenization cache hit (same input)
    print("\n--- Tokenization Cache (same input) ---")
    r3 = benchmark(
        lambda: direct_inference(params, model_cache, use_static_cache=False),
        "token_cache_hit",
        num_runs=5
    )
    results.append(r3)

    # Print summary
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"\n{'Method':<25} {'Mean (ms)':<12} {'Std (ms)':<10}")
    print("-"*50)
    for r in results:
        print(f"{r['name']:<25} {r['mean']:>10.1f} {r['std']:>10.1f}")

    # Speedups
    if len(results) >= 2:
        speedup = results[0]['mean'] / results[1]['mean']
        print(f"\nStatic cache speedup: {speedup:.2f}x")


if __name__ == "__main__":
    main()
