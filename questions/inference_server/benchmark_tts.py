#!/usr/bin/env python3
"""Benchmark helper for Kokoro TTS optimizations with optional WER guard."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import tempfile
import time
from typing import Callable, Optional

import numpy as np

try:
    import soundfile as sf
except Exception:
    sf = None

from questions.inference_server.optimized_inference import OptimizedKokoroTTS


def safe_average(times):
    return sum(times) / len(times) if times else 0.0


def percentile(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(len(ordered) * p)
    if idx >= len(ordered):
        idx = len(ordered) - 1
    return ordered[idx]


def percentile95(values):
    return percentile(values, 0.95)


def percentile99(values):
    return percentile(values, 0.99)


def normalize_for_wer(text: str) -> str:
    return "".join(ch for ch in (text or "").lower() if ch.isalnum() or ch.isspace()).strip()


def compute_wer(reference: str, hypothesis: str) -> float:
    ref = normalize_for_wer(reference).split()
    hyp = normalize_for_wer(hypothesis).split()
    if not ref:
        return 0.0 if not hyp else 1.0

    matrix = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for i in range(len(ref) + 1):
        matrix[i][0] = i
    for j in range(len(hyp) + 1):
        matrix[0][j] = j

    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            matrix[i][j] = min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + cost)

    return matrix[len(ref)][len(hyp)] / len(ref)


def transcribe_roundtrip_audio(asr_server_url: str, audio: np.ndarray, sample_rate: int = 24000) -> Optional[str]:
    if sf is None:
        print("  roundtrip-wer skipped: soundfile is not installed", flush=True)
        return None

    url = asr_server_url.rstrip("/")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, sample_rate, subtype="PCM_16")
        wav_path = f.name

    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-X",
                "POST",
                "--max-time",
                "30",
                f"{url}/api/v1/audio-file-extraction",
                "-F",
                f"audio_file=@{wav_path}",
                "-F",
                "translate_to_english=false",
                "-F",
                "include_segments=false",
            ],
            capture_output=True,
            text=True,
            timeout=35,
        )
        if result.returncode != 0:
            print(f"  roundtrip-wer failed: curl rc={result.returncode}", flush=True)
            return None
        payload = json.loads(result.stdout or "{}")
        return (payload.get("text") or "").strip()
    except Exception as exc:
        print(f"  roundtrip-wer failed: {exc}", flush=True)
        return None
    finally:
        try:
            os.unlink(wav_path)
        except Exception:
            pass


def benchmark_fn(label: str, fn: Callable[[], np.ndarray], runs: int, warmup: int = 1):
    if runs < 1:
        raise ValueError("--runs must be >= 1")

    # Warmup before timed runs to include model load and first-run initialization.
    for _ in range(max(0, warmup)):
        fn()

    times = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    times_ms = [t * 1000 for t in times]
    print(f"=== {label} ===")
    print(f"  runs: {runs}")
    print(f"  mean: {statistics.mean(times_ms):.2f}ms")
    print(f"  p95:  {percentile95(times_ms):.2f}ms")
    print(f"  p99:  {percentile99(times_ms):.2f}ms")
    print(f"  min:  {min(times_ms):.2f}ms")
    print(f"  max:  {max(times_ms):.2f}ms")
    print(f"  avg (s): {safe_average(times):.4f}")
    return {
        "runs": runs,
        "mean_ms": statistics.mean(times_ms),
        "p95_ms": percentile95(times_ms),
        "p99_ms": percentile99(times_ms),
        "min_ms": min(times_ms),
        "max_ms": max(times_ms),
    }


def run_roundtrip_wer(label: str, fn: Callable[[], np.ndarray], reference: str, asr_server_url: str):
    print(f"=== {label} roundtrip WER ===")
    generated = fn()
    if generated is None or len(generated) == 0:
        print("  no output audio generated")
        return None

    hypothesis = transcribe_roundtrip_audio(asr_server_url, generated, sample_rate=24000)
    if not hypothesis:
        print("  no transcription returned for roundtrip WER check")
        return None

    wer = compute_wer(reference, hypothesis)
    print(f"  reference: {reference}")
    print(f"  hypothesis: {hypothesis}")
    print(f"  WER: {wer:.4f}")
    return wer


def main():
    parser = argparse.ArgumentParser(description="Benchmark Kokoro TTS inference latency")
    parser.add_argument(
        "--text",
        default="Hello, this is a quick benchmark for accessibility-focused voice typing.",
        help="Text used for benchmarking",
    )
    parser.add_argument("--voice", default="af_nicole", help="Voice ID to use")
    parser.add_argument("--speed", type=float, default=1.0, help="TTS speed")
    parser.add_argument("--runs", type=int, default=5, help="Number of timed runs (>= 1)")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs before timing")
    parser.add_argument(
        "--mode",
        choices=["single", "batch", "both"],
        default="both",
        help="Benchmark mode",
    )
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size for batch mode")
    parser.add_argument("--no-compile", action="store_true", help="Disable CUDA graph/overlap optimization")
    parser.add_argument(
        "--torch-compile",
        action="store_true",
        help="Enable torch.compile optimization (requires compatible GPU/toolchain)",
    )
    parser.add_argument(
        "--check-wer",
        action="store_true",
        help="Run one single-mode roundtrip ASR check (text->tts->asr) to confirm WER impact",
    )
    parser.add_argument(
        "--asr-server",
        default=os.environ.get("ASR_SERVER_URL", "http://localhost:4444"),
        help="ASR endpoint for optional roundtrip WER check",
    )
    parser.add_argument(
        "--reference-text",
        help="Reference text for WER roundtrip check (defaults to --text)",
    )
    args = parser.parse_args()

    enable_torch_compile = args.torch_compile and not args.no_compile
    if args.no_compile and args.torch_compile:
        print("  note: --torch-compile ignored because --no-compile was set")

    tts = OptimizedKokoroTTS(
        enable_cuda_graphs=not args.no_compile,
        enable_overlap=not args.no_compile,
        enable_torch_compile=enable_torch_compile,
    )

    print(
        "=== config ===\n"
        f"  voice: {args.voice}\n"
        f"  speed: {args.speed}\n"
        f"  mode: {args.mode}\n"
        f"  runs: {args.runs}\n"
        f"  warmup: {args.warmup}\n"
        f"  cuda_graphs: {tts.enable_cuda_graphs}\n"
        f"  overlap: {tts.enable_overlap}\n"
        f"  torch_compile: {enable_torch_compile}\n"
    )

    single_stats = None
    if args.mode in {"single", "both"}:
        single_stats = benchmark_fn(
            "single: generate",
            lambda: tts.generate(args.text, voice=args.voice, speed=args.speed),
            runs=args.runs,
            warmup=args.warmup,
        )

    if args.mode in {"batch", "both"}:
        batch = [f"{args.text} #{i + 1}" for i in range(max(1, args.batch_size))]
        benchmark_fn(
            f"batch: {len(batch)} texts",
            lambda: tts.generate_batch(batch, voice=args.voice, speed=args.speed),
            runs=args.runs,
            warmup=args.warmup,
        )

    if args.check_wer and args.mode in {"single", "both"}:
        reference = args.reference_text or args.text
        run_roundtrip_wer(
            "single",
            lambda: tts.generate(args.text, voice=args.voice, speed=args.speed),
            reference=reference,
            asr_server_url=args.asr_server,
        )

    if single_stats is not None and args.mode in {"both", "single"}:
        print("=== single-mode timing summary ===")
        print(f"  mean_ms: {single_stats['mean_ms']:.2f}")
        print(f"  p95_ms: {single_stats['p95_ms']:.2f}")


if __name__ == "__main__":
    main()
