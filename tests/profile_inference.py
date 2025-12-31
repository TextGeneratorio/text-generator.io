#!/usr/bin/env python
"""
Quick profiling script using cProfile - no sudo required.

Generates:
- cProfile stats file (for snakeviz visualization)
- Text summary of hotspots
- Simple flame graph via flameprof (if installed)

Usage:
    # Run profiling
    PYTHONPATH=. python tests/profile_inference.py

    # View results with snakeviz (interactive browser view)
    snakeviz profiles/profile_*.prof

    # Generate flame graph from profile
    pip install flameprof
    flameprof profiles/profile_*.prof > profiles/flamegraph.svg
"""

import cProfile
import os
import pstats
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def profile_text_generation():
    """Profile text generation inference."""
    import torch
    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import fast_inference

    print("Setting up profiling environment...")

    model_cache = ModelCache()

    # Test parameters
    params = GenerateParams(
        text="Once upon a time in a galaxy far, far away",
        max_length=100,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        number_of_results=1,
        model="any",
    )

    # Warmup
    print("Running warmup...")
    for _ in range(2):
        fast_inference(params, model_cache)
        if torch.cuda.is_available():
            torch.cuda.synchronize()

    print("Starting profiled runs...")

    # Profile multiple runs
    for i in range(5):
        result = fast_inference(params, model_cache)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        print(f"  Run {i+1}/5 complete")

    return result


def main():
    output_dir = Path("profiles")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    profile_path = output_dir / f"profile_{timestamp}.prof"
    stats_path = output_dir / f"stats_{timestamp}.txt"

    print("="*60)
    print("INFERENCE PROFILING")
    print("="*60)

    # Run with cProfile
    profiler = cProfile.Profile()
    profiler.enable()

    profile_text_generation()

    profiler.disable()

    # Save binary profile for snakeviz
    profiler.dump_stats(str(profile_path))
    print(f"\nProfile saved to: {profile_path}")
    print(f"View with: snakeviz {profile_path}")

    # Generate text stats
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("cumulative")

    # Print top 30 functions
    print("\n" + "="*60)
    print("TOP 30 FUNCTIONS BY CUMULATIVE TIME")
    print("="*60 + "\n")

    stream.truncate(0)
    stream.seek(0)
    stats.print_stats(30)
    print(stream.getvalue())

    # Save full stats
    with open(stats_path, "w") as f:
        stream.truncate(0)
        stream.seek(0)
        stats.print_stats()
        f.write(stream.getvalue())

        f.write("\n\n" + "="*60 + "\n")
        f.write("CALLERS\n")
        f.write("="*60 + "\n\n")
        stream.truncate(0)
        stream.seek(0)
        stats.print_callers()
        f.write(stream.getvalue())

    print(f"Full stats saved to: {stats_path}")

    # Component analysis
    print("\n" + "="*60)
    print("COMPONENT BREAKDOWN")
    print("="*60)

    component_times = {
        "torch": 0.0,
        "transformers": 0.0,
        "accelerate": 0.0,
        "custom": 0.0,
        "other": 0.0,
    }

    all_stats = profiler.getstats()
    total_time = 0.0

    for stat in all_stats:
        func_name = str(stat.code) if hasattr(stat.code, '__name__') else str(stat.code)
        time = stat.totaltime

        if "torch" in func_name.lower():
            component_times["torch"] += time
        elif "transformers" in func_name.lower():
            component_times["transformers"] += time
        elif "accelerate" in func_name.lower():
            component_times["accelerate"] += time
        elif "questions/" in func_name or "/tests/" in func_name:
            component_times["custom"] += time
        else:
            component_times["other"] += time

        total_time += time

    if total_time > 0:
        print(f"\n{'Component':<20} {'Time (s)':<12} {'Percentage'}")
        print("-"*50)
        for component, time in sorted(component_times.items(), key=lambda x: -x[1]):
            pct = (time / total_time) * 100
            bar = "█" * int(pct / 2)
            print(f"{component:<20} {time:>10.3f}s   {pct:>5.1f}% {bar}")

    # Next steps
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print(f"""
1. View interactive profile:
   snakeviz {profile_path}

2. Generate flame graph (install flameprof first):
   pip install flameprof
   flameprof {profile_path} > profiles/flamegraph_{timestamp}.svg

3. For more detailed GPU profiling with py-spy (requires sudo):
   sudo python tests/benchmark_inference.py --flamegraph

4. For PyTorch profiler with CUDA timeline:
   python tests/torch_profiler.py
""")


if __name__ == "__main__":
    main()
