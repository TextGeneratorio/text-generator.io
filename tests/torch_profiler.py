#!/usr/bin/env python
"""
PyTorch Native Profiler for detailed CUDA and operator analysis.

Features:
- CUDA kernel-level timing
- Memory allocation tracking
- Operator breakdown
- TensorBoard integration
- Chrome trace export

Usage:
    # Basic run
    PYTHONPATH=. python tests/torch_profiler.py

    # View in TensorBoard
    tensorboard --logdir=profiles/torch_profiler

    # View Chrome trace in chrome://tracing
    # Open profiles/trace_*.json
"""

import gc
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from torch.profiler import ProfilerActivity, profile, record_function, schedule


def run_inference_workload(model_cache, params, num_runs: int = 5):
    """Run the inference workload to be profiled."""
    from questions.text_generator_inference import fast_inference

    results = []
    for i in range(num_runs):
        with record_function(f"inference_run_{i}"):
            result = fast_inference(params, model_cache)
            results.append(result)
    return results


def profile_with_torch_profiler():
    """Profile using PyTorch's built-in profiler."""
    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import fast_inference

    output_dir = Path("profiles/torch_profiler")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("="*60)
    print("PYTORCH PROFILER")
    print("="*60)

    # Setup
    model_cache = ModelCache()
    params = GenerateParams(
        text="The future of artificial intelligence is",
        max_length=100,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        number_of_results=1,
        model="any",
    )

    # Determine activities to trace
    activities = [ProfilerActivity.CPU]
    if torch.cuda.is_available():
        activities.append(ProfilerActivity.CUDA)
        print(f"CUDA available: {torch.cuda.get_device_name(0)}")

    # Warmup (outside profiler)
    print("\nWarmup runs...")
    for _ in range(2):
        fast_inference(params, model_cache)
        if torch.cuda.is_available():
            torch.cuda.synchronize()

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    print("\nProfiling...")

    # Profile with schedule: wait 1, warmup 1, active 3, repeat 1
    with profile(
        activities=activities,
        schedule=schedule(wait=1, warmup=1, active=3, repeat=1),
        on_trace_ready=torch.profiler.tensorboard_trace_handler(str(output_dir)),
        record_shapes=True,
        profile_memory=True,
        with_stack=True,
        with_flops=True,
    ) as prof:
        for step in range(5):
            with record_function(f"step_{step}"):
                result = fast_inference(params, model_cache)
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
            prof.step()
            print(f"  Step {step + 1}/5 complete")

    # Export Chrome trace
    trace_path = output_dir / f"trace_{timestamp}.json"
    prof.export_chrome_trace(str(trace_path))
    print(f"\nChrome trace saved to: {trace_path}")

    # Print summary tables
    print("\n" + "="*60)
    print("TOP CUDA KERNELS BY TIME (if CUDA available)")
    print("="*60)
    try:
        print(prof.key_averages().table(
            sort_by="cuda_time_total" if torch.cuda.is_available() else "cpu_time_total",
            row_limit=20
        ))
    except Exception as e:
        print(f"Could not generate CUDA table: {e}")

    print("\n" + "="*60)
    print("TOP CPU OPERATIONS")
    print("="*60)
    print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=20))

    print("\n" + "="*60)
    print("MEMORY USAGE")
    print("="*60)
    print(prof.key_averages().table(sort_by="self_cpu_memory_usage", row_limit=15))

    # Detailed operator analysis
    print("\n" + "="*60)
    print("OPERATOR BREAKDOWN")
    print("="*60)

    operator_stats = {}
    for event in prof.key_averages():
        op_name = event.key
        # Group by operator type
        op_type = op_name.split("::")[0] if "::" in op_name else op_name.split("_")[0]

        if op_type not in operator_stats:
            operator_stats[op_type] = {
                "cpu_time": 0,
                "cuda_time": 0,
                "count": 0,
                "cpu_memory": 0,
                "cuda_memory": 0,
            }

        operator_stats[op_type]["cpu_time"] += event.cpu_time_total
        operator_stats[op_type]["cuda_time"] += event.cuda_time_total if hasattr(event, 'cuda_time_total') else 0
        operator_stats[op_type]["count"] += event.count
        operator_stats[op_type]["cpu_memory"] += event.cpu_memory_usage
        operator_stats[op_type]["cuda_memory"] += event.cuda_memory_usage if hasattr(event, 'cuda_memory_usage') else 0

    # Sort by total time
    sorted_ops = sorted(
        operator_stats.items(),
        key=lambda x: x[1]["cpu_time"] + x[1].get("cuda_time", 0),
        reverse=True
    )[:20]

    print(f"\n{'Operator Type':<30} {'CPU (ms)':<12} {'CUDA (ms)':<12} {'Count':<8}")
    print("-"*70)
    for op_type, stats in sorted_ops:
        cpu_ms = stats["cpu_time"] / 1000
        cuda_ms = stats["cuda_time"] / 1000
        print(f"{op_type[:28]:<30} {cpu_ms:>10.2f} {cuda_ms:>10.2f} {stats['count']:>8}")

    # Export stats to JSON
    stats_path = output_dir / f"stats_{timestamp}.json"
    export_stats = {
        "timestamp": timestamp,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "pytorch_version": torch.__version__,
        "operators": {k: {
            "cpu_time_ms": v["cpu_time"] / 1000,
            "cuda_time_ms": v["cuda_time"] / 1000,
            "count": v["count"]
        } for k, v in sorted_ops}
    }
    with open(stats_path, "w") as f:
        json.dump(export_stats, f, indent=2)

    # Print recommendations
    print("\n" + "="*60)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("="*60)

    recommendations = analyze_profile_for_recommendations(prof, operator_stats)
    for rec in recommendations:
        print(f"\n{rec}")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print(f"""
1. View in TensorBoard:
   tensorboard --logdir={output_dir}
   Open http://localhost:6006 in browser

2. View Chrome trace:
   Open chrome://tracing in Chrome
   Load: {trace_path}

3. Detailed stats:
   {stats_path}
""")

    return prof


def analyze_profile_for_recommendations(prof, operator_stats) -> list:
    """Analyze profile and generate optimization recommendations."""
    recommendations = []

    # Get total times
    total_cpu = sum(s["cpu_time"] for s in operator_stats.values())
    total_cuda = sum(s["cuda_time"] for s in operator_stats.values())

    # Check for memory-bound operations
    for op_type, stats in operator_stats.items():
        if "copy" in op_type.lower() or "to" in op_type.lower():
            pct = (stats["cpu_time"] + stats["cuda_time"]) / (total_cpu + total_cuda + 1) * 100
            if pct > 5:
                recommendations.append(
                    f"⚠️  Memory copy operations taking {pct:.1f}% of time\n"
                    "   Consider:\n"
                    "   - Keeping tensors on GPU (avoid .cpu()/.cuda() calls)\n"
                    "   - Using pin_memory=True for DataLoader\n"
                    "   - Batching small tensors together"
                )

        if "matmul" in op_type.lower() or "mm" in op_type.lower() or "linear" in op_type.lower():
            if stats["cuda_time"] < stats["cpu_time"] * 0.5 and total_cuda > 0:
                recommendations.append(
                    f"⚠️  Matrix operations ({op_type}) have low GPU utilization\n"
                    "   Consider:\n"
                    "   - Increasing batch size\n"
                    "   - Using torch.compile() for kernel fusion\n"
                    "   - Enabling TF32 for Ampere GPUs"
                )

    # Check for attention operations
    attention_time = sum(
        s["cuda_time"] + s["cpu_time"]
        for op, s in operator_stats.items()
        if "attention" in op.lower() or "sdpa" in op.lower()
    )
    if attention_time > 0:
        attention_pct = attention_time / (total_cpu + total_cuda + 1) * 100
        if attention_pct > 20:
            recommendations.append(
                f"⚠️  Attention operations taking {attention_pct:.1f}% of time\n"
                "   Consider:\n"
                "   - Enabling Flash Attention 2: model.to(torch.bfloat16).enable_flash_attention()\n"
                "   - Using torch.nn.functional.scaled_dot_product_attention\n"
                "   - Reducing sequence length with sliding window attention"
            )

    # Check GPU memory
    if torch.cuda.is_available():
        peak_memory = torch.cuda.max_memory_allocated() / 1e9
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        if peak_memory > total_memory * 0.8:
            recommendations.append(
                f"⚠️  High GPU memory usage: {peak_memory:.1f}GB / {total_memory:.1f}GB\n"
                "   Consider:\n"
                "   - Using gradient checkpointing\n"
                "   - Reducing batch size\n"
                "   - Using 8-bit or 4-bit quantization"
            )

    if not recommendations:
        recommendations.append(
            "✅ Profile looks healthy! For further optimization:\n"
            "   - Try torch.compile() for 2x+ speedup\n"
            "   - Consider model quantization (INT8/FP16)\n"
            "   - Use Flash Attention if available"
        )

    return recommendations


def quick_benchmark():
    """Quick benchmark without full profiling."""
    import time
    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import fast_inference

    print("="*60)
    print("QUICK BENCHMARK")
    print("="*60)

    model_cache = ModelCache()
    params = GenerateParams(
        text="The quick brown fox jumps over",
        max_length=50,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        number_of_results=1,
        model="any",
    )

    # Warmup
    print("\nWarmup...")
    for _ in range(2):
        fast_inference(params, model_cache)

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()

    # Benchmark
    times = []
    print("Benchmarking...")
    for i in range(10):
        start = time.perf_counter()
        result = fast_inference(params, model_cache)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        end = time.perf_counter()
        times.append(end - start)
        print(f"  Run {i+1}/10: {(end-start)*1000:.1f}ms")

    import statistics
    print(f"\nResults:")
    print(f"  Mean: {statistics.mean(times)*1000:.1f}ms")
    print(f"  Std:  {statistics.stdev(times)*1000:.1f}ms")
    print(f"  Min:  {min(times)*1000:.1f}ms")
    print(f"  Max:  {max(times)*1000:.1f}ms")

    if torch.cuda.is_available():
        print(f"\n  GPU Memory Peak: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PyTorch profiler for inference")
    parser.add_argument("--quick", action="store_true", help="Quick benchmark only")
    args = parser.parse_args()

    if args.quick:
        quick_benchmark()
    else:
        profile_with_torch_profiler()


if __name__ == "__main__":
    main()
