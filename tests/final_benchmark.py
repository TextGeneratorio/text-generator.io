#!/usr/bin/env python
"""Final benchmark comparing different inference paths."""

import gc
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch


def benchmark_inference(inference_fn, model_cache, params, name, num_runs=5):
    """Benchmark an inference function."""
    # Warmup
    print(f"\n{name}: Warmup...")
    inference_fn(params, model_cache)
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Benchmark
    times = []
    print(f"{name}: Benchmarking {num_runs} runs...")
    for i in range(num_runs):
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        start = time.perf_counter()

        result = inference_fn(params, model_cache)

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        end = time.perf_counter()

        elapsed = (end - start) * 1000
        times.append(elapsed)
        print(f"  Run {i+1}/{num_runs}: {elapsed:.1f}ms")

    return {
        "name": name,
        "mean": statistics.mean(times),
        "std": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "times": times,
    }


def main():
    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import direct_inference, fast_inference

    print("="*60)
    print("FINAL BENCHMARK COMPARISON")
    print("="*60)

    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA: {torch.version.cuda}")
    print(f"PyTorch: {torch.__version__}")

    model_cache = ModelCache()

    # Test parameters - short generation
    params = GenerateParams(
        text="Once upon a time",
        max_length=30,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        number_of_results=1,
        model="any",
    )

    results = []

    # Benchmark original fast_inference
    print("\n" + "-"*60)
    result1 = benchmark_inference(fast_inference, model_cache, params,
                                  "fast_inference (pipeline)", num_runs=5)
    results.append(result1)

    # Benchmark direct_inference
    print("\n" + "-"*60)
    result2 = benchmark_inference(direct_inference, model_cache, params,
                                  "direct_inference (no pipeline)", num_runs=5)
    results.append(result2)

    # Print comparison
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"\n{'Method':<35} {'Mean (ms)':<12} {'Std (ms)':<10} {'Min (ms)':<10} {'Max (ms)':<10}")
    print("-"*77)
    for r in results:
        print(f"{r['name']:<35} {r['mean']:>10.1f} {r['std']:>10.1f} {r['min']:>10.1f} {r['max']:>10.1f}")

    # Calculate speedup
    if len(results) >= 2:
        speedup = results[0]['mean'] / results[1]['mean']
        print(f"\nSpeedup from direct_inference: {speedup:.2f}x")

    if torch.cuda.is_available():
        print(f"\nGPU Memory Peak: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
