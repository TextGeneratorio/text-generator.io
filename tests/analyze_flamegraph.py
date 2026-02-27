#!/usr/bin/env python
"""
Flame Graph Analysis Tool

Analyzes py-spy output (speedscope JSON format) to identify:
- Hotspots in the code
- Time spent in different components (torch, transformers, custom code)
- Optimization recommendations

Usage:
    python tests/analyze_flamegraph.py profiles/speedscope_*.json
"""

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class FrameStats:
    """Statistics for a single frame/function."""
    name: str
    file: str
    line: int
    self_time: float  # Time spent in this frame (not children)
    total_time: float  # Time including children
    call_count: int


class FlameGraphAnalyzer:
    """Analyze speedscope JSON profiles for optimization opportunities."""

    COMPONENT_PATTERNS = {
        "torch": ["torch/", "torch."],
        "transformers": ["transformers/"],
        "accelerate": ["accelerate/"],
        "cuda": ["cuda", "cublas", "cudnn", "nccl"],
        "numpy": ["numpy/"],
        "custom": [],  # Catchall for project code
    }

    def __init__(self, profile_path: str):
        self.profile_path = profile_path
        self.frames: Dict[str, FrameStats] = {}
        self.component_times: Dict[str, float] = defaultdict(float)
        self.total_samples = 0
        self.sample_rate = 100  # Default py-spy rate

    def load_profile(self):
        """Load and parse the speedscope JSON profile."""
        with open(self.profile_path, "r") as f:
            data = json.load(f)

        # Get the frame table
        if "shared" in data:
            frames = data["shared"]["frames"]
        elif "$schema" in data and "speedscope" in data["$schema"]:
            frames = data.get("shared", {}).get("frames", [])
        else:
            print("Unknown profile format")
            return

        # Parse profiles
        profiles = data.get("profiles", [])
        if not profiles:
            print("No profiles found in the data")
            return

        # Process each profile
        for profile in profiles:
            profile_type = profile.get("type", "")
            if profile_type == "sampled":
                self._process_sampled_profile(profile, frames)
            elif profile_type == "evented":
                self._process_evented_profile(profile, frames)

    def _process_sampled_profile(self, profile: Dict, frames: List[Dict]):
        """Process a sampled profile."""
        samples = profile.get("samples", [])
        weights = profile.get("weights", [])

        if not weights:
            weights = [1] * len(samples)

        frame_times = defaultdict(float)
        self.total_samples = sum(weights)

        for sample, weight in zip(samples, weights):
            # Each sample is a list of frame indices (call stack)
            for i, frame_idx in enumerate(sample):
                if frame_idx < len(frames):
                    frame = frames[frame_idx]
                    frame_name = frame.get("name", "unknown")

                    # Self time is only for the last frame in the stack
                    if i == len(sample) - 1:
                        frame_times[frame_name] += weight

        # Convert to FrameStats
        for name, time in frame_times.items():
            self.frames[name] = FrameStats(
                name=name,
                file="",
                line=0,
                self_time=time,
                total_time=time,
                call_count=int(time)
            )

    def _process_evented_profile(self, profile: Dict, frames: List[Dict]):
        """Process an evented profile."""
        events = profile.get("events", [])
        start_times = {}
        frame_times = defaultdict(float)

        for event in events:
            event_type = event.get("type", "")
            frame_idx = event.get("frame", 0)
            at = event.get("at", 0)

            if frame_idx < len(frames):
                frame_name = frames[frame_idx].get("name", "unknown")

                if event_type == "O":  # Open
                    start_times[frame_idx] = at
                elif event_type == "C":  # Close
                    if frame_idx in start_times:
                        duration = at - start_times[frame_idx]
                        frame_times[frame_name] += duration
                        del start_times[frame_idx]

        # Convert to FrameStats
        for name, time in frame_times.items():
            self.frames[name] = FrameStats(
                name=name,
                file="",
                line=0,
                self_time=time,
                total_time=time,
                call_count=1
            )
            self.total_samples += time

    def categorize_frames(self):
        """Categorize frames by component."""
        for frame_name, stats in self.frames.items():
            component = self._get_component(frame_name)
            self.component_times[component] += stats.self_time

    def _get_component(self, frame_name: str) -> str:
        """Determine which component a frame belongs to."""
        frame_lower = frame_name.lower()

        for component, patterns in self.COMPONENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in frame_lower:
                    return component

        # Check if it's from our project
        if "questions/" in frame_name or "inference" in frame_lower:
            return "custom"

        return "other"

    def get_top_hotspots(self, n: int = 20) -> List[Tuple[str, float]]:
        """Get the top N hotspots by self time."""
        sorted_frames = sorted(
            self.frames.items(),
            key=lambda x: x[1].self_time,
            reverse=True
        )
        return [(name, stats.self_time / self.total_samples * 100)
                for name, stats in sorted_frames[:n]]

    def analyze(self) -> Dict:
        """Perform full analysis and return results."""
        self.load_profile()
        self.categorize_frames()

        total_time = sum(self.component_times.values())
        if total_time == 0:
            total_time = 1  # Avoid division by zero

        component_percentages = {
            component: time / total_time * 100
            for component, time in self.component_times.items()
        }

        return {
            "total_samples": self.total_samples,
            "component_breakdown": component_percentages,
            "hotspots": self.get_top_hotspots(20),
        }

    def print_report(self):
        """Print a formatted analysis report."""
        results = self.analyze()

        print("\n" + "="*70)
        print("FLAME GRAPH ANALYSIS REPORT")
        print("="*70)
        print(f"\nProfile: {self.profile_path}")
        print(f"Total Samples: {results['total_samples']}")

        print("\n" + "-"*70)
        print("COMPONENT BREAKDOWN")
        print("-"*70)
        print(f"{'Component':<20} {'Time %':<15} {'Bar'}")
        print("-"*70)

        breakdown = sorted(
            results["component_breakdown"].items(),
            key=lambda x: x[1],
            reverse=True
        )

        for component, pct in breakdown:
            bar = "█" * int(pct / 2)
            print(f"{component:<20} {pct:>10.1f}%    {bar}")

        print("\n" + "-"*70)
        print("TOP 20 HOTSPOTS")
        print("-"*70)
        print(f"{'Rank':<6} {'Function':<50} {'Time %':<10}")
        print("-"*70)

        for i, (name, pct) in enumerate(results["hotspots"], 1):
            # Truncate long names
            display_name = name[:47] + "..." if len(name) > 50 else name
            print(f"{i:<6} {display_name:<50} {pct:>8.2f}%")

        self._print_optimization_recommendations(results)

    def _print_optimization_recommendations(self, results: Dict):
        """Print optimization recommendations based on analysis."""
        print("\n" + "="*70)
        print("OPTIMIZATION RECOMMENDATIONS")
        print("="*70)

        recommendations = []
        breakdown = results["component_breakdown"]

        # Check torch/CUDA usage
        cuda_pct = breakdown.get("cuda", 0)
        torch_pct = breakdown.get("torch", 0)

        if cuda_pct < 30 and torch_pct > 40:
            recommendations.append(
                "⚠️  Low CUDA utilization ({:.1f}%) with high PyTorch time ({:.1f}%)\n"
                "   Consider:\n"
                "   - Using torch.compile() for model compilation\n"
                "   - Enabling Flash Attention if supported\n"
                "   - Using larger batch sizes to improve GPU utilization\n"
                "   - Profile with nvprof/nsight for CUDA-specific bottlenecks"
                .format(cuda_pct, torch_pct)
            )

        # Check transformers overhead
        transformers_pct = breakdown.get("transformers", 0)
        if transformers_pct > 50:
            recommendations.append(
                "⚠️  High transformers overhead ({:.1f}%)\n"
                "   Consider:\n"
                "   - Using optimized inference backends (vLLM, TensorRT-LLM)\n"
                "   - Enabling BetterTransformer optimizations\n"
                "   - Using torch.compile() with the model"
                .format(transformers_pct)
            )

        # Check custom code
        custom_pct = breakdown.get("custom", 0)
        if custom_pct > 20:
            recommendations.append(
                "⚠️  Significant time in custom code ({:.1f}%)\n"
                "   Review hotspots above to identify specific functions to optimize.\n"
                "   Consider:\n"
                "   - Caching repeated computations\n"
                "   - Using torch.no_grad() / torch.inference_mode()\n"
                "   - Vectorizing loops with numpy/torch operations"
                .format(custom_pct)
            )

        # Check for specific hotspots
        hotspots = results["hotspots"]
        for name, pct in hotspots[:5]:
            name_lower = name.lower()
            if "tokeniz" in name_lower and pct > 5:
                recommendations.append(
                    f"⚠️  Tokenization taking {pct:.1f}% of time\n"
                    "   Consider:\n"
                    "   - Using fast tokenizers (PreTrainedTokenizerFast)\n"
                    "   - Batch tokenization\n"
                    "   - Pre-tokenizing common prompts"
                )
            if "attention" in name_lower and pct > 10:
                recommendations.append(
                    f"⚠️  Attention operations taking {pct:.1f}% of time\n"
                    "   Consider:\n"
                    "   - Enabling Flash Attention 2\n"
                    "   - Using scaled_dot_product_attention\n"
                    "   - Reducing sequence length where possible"
                )

        if recommendations:
            for rec in recommendations:
                print(f"\n{rec}")
        else:
            print("\n✅ No major issues detected. Profile looks healthy.")
            print("   For further optimization, consider:")
            print("   - Using torch.compile() for 2x+ speedups")
            print("   - Quantization (INT8/FP16/BF16)")
            print("   - Model distillation for smaller models")

        print("\n" + "="*70)


def compare_profiles(profile_paths: List[str]):
    """Compare multiple profiles to track performance changes."""
    print("\n" + "="*70)
    print("PROFILE COMPARISON")
    print("="*70)

    analyses = []
    for path in profile_paths:
        analyzer = FlameGraphAnalyzer(path)
        results = analyzer.analyze()
        results["path"] = path
        analyses.append(results)

    # Compare component breakdowns
    print(f"\n{'Profile':<40} ", end="")
    components = set()
    for a in analyses:
        components.update(a["component_breakdown"].keys())

    for comp in sorted(components):
        print(f"{comp:<12}", end="")
    print()

    for a in analyses:
        name = Path(a["path"]).stem[:38]
        print(f"{name:<40} ", end="")
        for comp in sorted(components):
            pct = a["component_breakdown"].get(comp, 0)
            print(f"{pct:>10.1f}% ", end="")
        print()


def main():
    parser = argparse.ArgumentParser(description="Analyze flame graph profiles")
    parser.add_argument("profiles", nargs="+", help="Speedscope JSON profile files to analyze")
    parser.add_argument("--compare", action="store_true",
                        help="Compare multiple profiles")

    args = parser.parse_args()

    if args.compare and len(args.profiles) > 1:
        compare_profiles(args.profiles)
    else:
        for profile_path in args.profiles:
            analyzer = FlameGraphAnalyzer(profile_path)
            analyzer.print_report()


if __name__ == "__main__":
    main()
