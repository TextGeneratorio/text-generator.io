#!/usr/bin/env python
"""
Benchmark and profiling script for inference performance analysis.

Features:
- Inference timing benchmarks with statistical analysis
- Flame graph generation via py-spy
- Memory profiling
- Throughput measurements (tokens/sec)
- Latency percentiles (p50, p95, p99)

Usage:
    # Basic benchmark run
    python tests/benchmark_inference.py

    # Run with flame graph (requires sudo for py-spy)
    sudo python tests/benchmark_inference.py --flamegraph

    # Run specific benchmark
    python tests/benchmark_inference.py --benchmark text_generation

    # Warm-up runs before benchmarking
    python tests/benchmark_inference.py --warmup 3
"""

import argparse
import gc
import json
import os
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch

# Ensure we can import from the project
from questions.models import GenerateParams


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    name: str
    iterations: int
    times: List[float] = field(default_factory=list)
    tokens_generated: List[int] = field(default_factory=list)
    memory_peak_mb: float = 0.0

    @property
    def mean_time(self) -> float:
        return statistics.mean(self.times) if self.times else 0.0

    @property
    def std_time(self) -> float:
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0

    @property
    def p50(self) -> float:
        return statistics.median(self.times) if self.times else 0.0

    @property
    def p95(self) -> float:
        if not self.times:
            return 0.0
        sorted_times = sorted(self.times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def p99(self) -> float:
        if not self.times:
            return 0.0
        sorted_times = sorted(self.times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def tokens_per_second(self) -> float:
        if not self.times or not self.tokens_generated:
            return 0.0
        total_tokens = sum(self.tokens_generated)
        total_time = sum(self.times)
        return total_tokens / total_time if total_time > 0 else 0.0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_time_ms": self.mean_time * 1000,
            "std_time_ms": self.std_time * 1000,
            "p50_ms": self.p50 * 1000,
            "p95_ms": self.p95 * 1000,
            "p99_ms": self.p99 * 1000,
            "tokens_per_second": self.tokens_per_second,
            "memory_peak_mb": self.memory_peak_mb,
            "min_time_ms": min(self.times) * 1000 if self.times else 0,
            "max_time_ms": max(self.times) * 1000 if self.times else 0,
        }


class InferenceBenchmark:
    """Benchmark suite for inference performance."""

    def __init__(self, warmup_runs: int = 2, iterations: int = 10):
        self.warmup_runs = warmup_runs
        self.iterations = iterations
        self.model_cache = None
        self.results: List[BenchmarkResult] = []

    def setup(self):
        """Initialize model cache and load models."""
        print("Setting up benchmark environment...")

        # Import here to avoid loading at import time
        from questions.inference_server.model_cache import ModelCache

        self.model_cache = ModelCache()

        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        print(f"  Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
        if torch.cuda.is_available():
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            print(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        print()

    def get_memory_usage(self) -> float:
        """Get current GPU memory usage in MB."""
        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / 1e6
        return 0.0

    def reset_memory_stats(self):
        """Reset GPU memory statistics."""
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

    def run_warmup(self, benchmark_fn, params):
        """Run warmup iterations to ensure models are loaded and compiled."""
        print(f"  Running {self.warmup_runs} warmup iterations...")
        for i in range(self.warmup_runs):
            benchmark_fn(params)
            gc.collect()

    def benchmark_text_generation(self, params: GenerateParams) -> BenchmarkResult:
        """Benchmark text generation inference."""
        from questions.text_generator_inference import fast_inference

        result = BenchmarkResult(
            name=f"text_generation_maxlen{params.max_length}",
            iterations=self.iterations
        )

        # Warmup
        self.run_warmup(lambda p: fast_inference(p, self.model_cache), params)

        # Reset memory stats
        self.reset_memory_stats()

        print(f"  Running {self.iterations} benchmark iterations...")
        for i in range(self.iterations):
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.synchronize()

            start = time.perf_counter()
            output = fast_inference(params, self.model_cache)

            if torch.cuda.is_available():
                torch.cuda.synchronize()
            end = time.perf_counter()

            elapsed = end - start
            result.times.append(elapsed)

            # Count tokens generated
            if output and len(output) > 0:
                generated_text = output[0].get("generated_text", "")
                # Rough token estimate (4 chars per token on average)
                tokens = len(generated_text.split())
                result.tokens_generated.append(tokens)

            print(f"    Iteration {i+1}/{self.iterations}: {elapsed*1000:.2f}ms")

        result.memory_peak_mb = self.get_memory_usage()
        return result

    def benchmark_audio_transcription(self) -> Optional[BenchmarkResult]:
        """Benchmark audio transcription (NeMo Parakeet)."""
        try:
            from questions.inference_server.inference_server import load_audio_model
        except ImportError:
            print("  Skipping audio benchmark - NeMo not available")
            return None

        result = BenchmarkResult(
            name="audio_transcription",
            iterations=self.iterations
        )

        # Create a small test audio file
        import numpy as np
        import tempfile
        try:
            import soundfile as sf
        except ImportError:
            print("  Skipping audio benchmark - soundfile not available")
            return None

        # Generate 2 seconds of silence/noise
        sample_rate = 16000
        duration = 2.0
        audio = np.random.randn(int(sample_rate * duration)) * 0.01

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, sample_rate)
            audio_path = f.name

        try:
            # Load model (warmup)
            audio_model = load_audio_model()

            self.reset_memory_stats()

            print(f"  Running {self.iterations} audio benchmark iterations...")
            for i in range(self.iterations):
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.synchronize()

                start = time.perf_counter()
                with torch.inference_mode():
                    _ = audio_model.transcribe([audio_path], timestamps=True)

                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                end = time.perf_counter()

                elapsed = end - start
                result.times.append(elapsed)
                print(f"    Iteration {i+1}/{self.iterations}: {elapsed*1000:.2f}ms")

            result.memory_peak_mb = self.get_memory_usage()
        finally:
            os.unlink(audio_path)

        return result

    def benchmark_tts(self) -> Optional[BenchmarkResult]:
        """Benchmark text-to-speech generation (Kokoro)."""
        try:
            from questions.inference_server.inference_server import audio_process, load_speechgen_model

            result = BenchmarkResult(
                name="text_to_speech",
                iterations=self.iterations
            )

            test_text = "Hello, this is a test of the text to speech system."

            # Warmup - load models
            print("  Loading TTS model...")
            self.model_cache.add_or_get("speech_model", load_speechgen_model)

            self.reset_memory_stats()

            print(f"  Running {self.iterations} TTS benchmark iterations...")
            for i in range(self.iterations):
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.synchronize()

                start = time.perf_counter()
                _ = audio_process(test_text, voice="af_nicole", speed=1.0)

                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                end = time.perf_counter()

                elapsed = end - start
                result.times.append(elapsed)
                print(f"    Iteration {i+1}/{self.iterations}: {elapsed*1000:.2f}ms")

            result.memory_peak_mb = self.get_memory_usage()
            return result

        except Exception as e:
            print(f"  Skipping TTS benchmark - {e}")
            return None

    def run_all_benchmarks(self, benchmarks: List[str] = None):
        """Run all specified benchmarks."""
        available_benchmarks = {
            "text_generation": self._run_text_generation_suite,
            "audio": self.benchmark_audio_transcription,
            "tts": self.benchmark_tts,
        }

        if benchmarks is None:
            benchmarks = ["text_generation"]  # Default to just text generation

        for name in benchmarks:
            if name in available_benchmarks:
                print(f"\n{'='*60}")
                print(f"Running benchmark: {name}")
                print('='*60)

                result = available_benchmarks[name]()
                if result:
                    if isinstance(result, list):
                        self.results.extend(result)
                    else:
                        self.results.append(result)

    def _run_text_generation_suite(self) -> List[BenchmarkResult]:
        """Run text generation with different configurations."""
        results = []

        test_configs = [
            {"max_length": 50, "prompt": "Once upon a time"},
            {"max_length": 100, "prompt": "The quick brown fox"},
            {"max_length": 200, "prompt": "In the beginning there was"},
        ]

        for config in test_configs:
            print(f"\n  Config: max_length={config['max_length']}")
            params = GenerateParams(
                text=config["prompt"],
                max_length=config["max_length"],
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                number_of_results=1,
                model="any",
            )
            result = self.benchmark_text_generation(params)
            results.append(result)

        return results

    def print_results(self):
        """Print benchmark results in a formatted table."""
        print("\n" + "="*80)
        print("BENCHMARK RESULTS")
        print("="*80)

        # Header
        print(f"{'Benchmark':<35} {'Mean (ms)':<12} {'Std (ms)':<10} {'P50 (ms)':<10} {'P95 (ms)':<10} {'Tok/s':<10}")
        print("-"*80)

        for result in self.results:
            print(f"{result.name:<35} {result.mean_time*1000:>10.2f} {result.std_time*1000:>10.2f} "
                  f"{result.p50*1000:>10.2f} {result.p95*1000:>10.2f} {result.tokens_per_second:>10.1f}")

        print("-"*80)
        print(f"\nDevice: {'CUDA - ' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
        if self.results and self.results[0].memory_peak_mb > 0:
            print(f"Peak GPU Memory: {self.results[0].memory_peak_mb:.1f} MB")

    def save_results(self, output_path: str):
        """Save results to JSON file."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
            "pytorch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "warmup_runs": self.warmup_runs,
            "iterations": self.iterations,
            "results": [r.to_dict() for r in self.results]
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nResults saved to {output_path}")


def run_with_flamegraph(script_args: List[str], output_dir: str = "profiles"):
    """Run the benchmark with py-spy to generate flame graphs."""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    flamegraph_path = os.path.join(output_dir, f"flamegraph_{timestamp}.svg")
    speedscope_path = os.path.join(output_dir, f"speedscope_{timestamp}.json")

    # Build the py-spy command
    python_path = sys.executable
    script_path = __file__

    # Create a temporary script that runs the benchmark
    benchmark_script = f"""
import sys
sys.path.insert(0, '{Path(__file__).parent.parent}')
from tests.benchmark_inference import InferenceBenchmark

benchmark = InferenceBenchmark(warmup_runs=1, iterations=5)
benchmark.setup()
benchmark.run_all_benchmarks(['text_generation'])
"""

    temp_script = os.path.join(output_dir, "temp_benchmark.py")
    with open(temp_script, "w") as f:
        f.write(benchmark_script)

    print(f"Generating flame graph...")
    print(f"Output: {flamegraph_path}")

    # Run py-spy record
    cmd = [
        "py-spy", "record",
        "--output", flamegraph_path,
        "--format", "flamegraph",
        "--rate", "100",  # 100 samples/sec
        "--native",  # Include native (C/CUDA) frames
        "--", python_path, temp_script
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"py-spy error: {result.stderr}")
            print("Note: py-spy may require sudo permissions")
        else:
            print(f"Flame graph saved to: {flamegraph_path}")
    except FileNotFoundError:
        print("py-spy not found. Install with: pip install py-spy")
    finally:
        if os.path.exists(temp_script):
            os.unlink(temp_script)

    # Also generate speedscope format for interactive analysis
    cmd_speedscope = [
        "py-spy", "record",
        "--output", speedscope_path,
        "--format", "speedscope",
        "--rate", "100",
        "--native",
        "--", python_path, temp_script
    ]

    temp_script2 = os.path.join(output_dir, "temp_benchmark2.py")
    with open(temp_script2, "w") as f:
        f.write(benchmark_script)

    cmd_speedscope[-1] = temp_script2

    try:
        result = subprocess.run(cmd_speedscope, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Speedscope profile saved to: {speedscope_path}")
            print(f"View at: https://www.speedscope.app/ (drag & drop the JSON file)")
    except Exception as e:
        print(f"Speedscope generation failed: {e}")
    finally:
        if os.path.exists(temp_script2):
            os.unlink(temp_script2)


def main():
    parser = argparse.ArgumentParser(description="Inference benchmark and profiling tool")
    parser.add_argument("--warmup", type=int, default=2, help="Number of warmup iterations")
    parser.add_argument("--iterations", type=int, default=10, help="Number of benchmark iterations")
    parser.add_argument("--benchmark", type=str, nargs="+",
                        choices=["text_generation", "audio", "tts"],
                        default=["text_generation"],
                        help="Which benchmarks to run")
    parser.add_argument("--flamegraph", action="store_true", help="Generate flame graph with py-spy")
    parser.add_argument("--output", type=str, default="benchmark_results.json",
                        help="Output file for results")
    parser.add_argument("--profile-dir", type=str, default="profiles",
                        help="Directory for profile outputs")

    args = parser.parse_args()

    if args.flamegraph:
        run_with_flamegraph(sys.argv, args.profile_dir)
        return

    # Run regular benchmark
    benchmark = InferenceBenchmark(
        warmup_runs=args.warmup,
        iterations=args.iterations
    )

    benchmark.setup()
    benchmark.run_all_benchmarks(args.benchmark)
    benchmark.print_results()
    benchmark.save_results(args.output)


if __name__ == "__main__":
    main()
