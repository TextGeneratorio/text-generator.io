#!/usr/bin/env python3
"""
Benchmark conservative TTS silence optimization against baseline output.

This script is intentionally strict for WER safety:
- By default it refuses GPU-based WER runs (CUDA ASR can be unstable).
- It supports repeated runs and a max allowed WER regression guard.

Usage:
  CUDA_VISIBLE_DEVICES='' PYTHONPATH=. .venv/bin/python tests/benchmarks/benchmark_tts_silence.py
"""

import argparse
import time
from tempfile import NamedTemporaryFile

import jiwer
import soundfile as sf
import torch

from questions.inference_server.inference_server import load_audio_model
from questions.inference_server.kokoro import generate_full
from questions.inference_server.models import build_model
from questions.inference_server.tts_utils import optimize_tts_audio_for_speed


TEST_TEXTS = [
    "Text Generator is bringing the cost of intelligence toward zero.",
    "The quick brown fox jumps over the lazy dog while five quacking zephyrs jolt my wax bed.",
    "This benchmark checks that trimming silence improves latency without hurting recognition quality.",
]


def transcribe_with_nemo(asr, audio, sample_rate=24000) -> str:
    with NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, audio, sample_rate)
        result = asr.transcribe([tmp.name], timestamps=False)
    if isinstance(result, list) and result:
        item = result[0]
        if isinstance(item, str):
            return item.strip()
        if hasattr(item, "text"):
            return str(item.text).strip()
    return str(result).strip()


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark TTS silence optimization with WER guard rails.")
    parser.add_argument("--repeats", type=int, default=2, help="Generation repeats per text for timing averages.")
    parser.add_argument(
        "--max-wer-delta",
        type=float,
        default=0.01,
        help="Fail if optimized WER exceeds baseline by more than this.",
    )
    parser.add_argument(
        "--allow-gpu-wer",
        action="store_true",
        help="Allow GPU ASR/WER runs. Disabled by default for stability.",
    )
    parser.add_argument("--trim-edges", action="store_true", default=True)
    parser.add_argument("--compress-internal", action="store_true", default=False)
    parser.add_argument("--edge-trim-ms", type=int, default=120)
    parser.add_argument("--internal-silence-min-ms", type=int, default=250)
    parser.add_argument("--internal-silence-keep-ms", type=int, default=80)
    parser.add_argument("--silence-threshold", type=int, default=64)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats must be >= 1")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not args.allow_gpu_wer:
        raise SystemExit(
            "Refusing GPU WER benchmark by default. Re-run with "
            "`CUDA_VISIBLE_DEVICES=''` for stable CPU WER, or pass --allow-gpu-wer."
        )

    model = build_model("models/kokoro-v0_19.pth", device)
    voicepack = torch.load("models/voices/af_nicole.pt", weights_only=True).to(device)
    asr = load_audio_model()

    print(f"Device: {device}, repeats={args.repeats}")
    print(
        "text_idx,baseline_gen_ms,postprocess_ms,baseline_dur_s,optimized_dur_s,"
        "baseline_wer,opt_wer,wer_delta"
    )

    worst_delta = 0.0

    for idx, text in enumerate(TEST_TEXTS, start=1):
        baseline_times = []
        baseline_audio = None
        for _ in range(args.repeats):
            t0 = time.perf_counter()
            baseline_audio, _ = generate_full(model, text, voicepack, lang="a", speed=1.0)
            baseline_times.append((time.perf_counter() - t0) * 1000)

        t1 = time.perf_counter()
        optimized_audio = optimize_tts_audio_for_speed(
            baseline_audio,
            sample_rate=24000,
            trim_edges=args.trim_edges,
            compress_internal=args.compress_internal,
            edge_trim_ms=args.edge_trim_ms,
            internal_silence_min_ms=args.internal_silence_min_ms,
            internal_silence_keep_ms=args.internal_silence_keep_ms,
            threshold=args.silence_threshold,
        )
        postprocess_ms = (time.perf_counter() - t1) * 1000

        baseline_transcript = transcribe_with_nemo(asr, baseline_audio)
        optimized_transcript = transcribe_with_nemo(asr, optimized_audio)

        reference = text.lower().strip()
        baseline_wer = jiwer.wer(reference, baseline_transcript.lower().strip())
        optimized_wer = jiwer.wer(reference, optimized_transcript.lower().strip())
        wer_delta = optimized_wer - baseline_wer
        worst_delta = max(worst_delta, wer_delta)

        baseline_dur_s = len(baseline_audio) / 24000.0
        optimized_dur_s = len(optimized_audio) / 24000.0

        print(
            f"{idx},{(sum(baseline_times) / len(baseline_times)):.2f},{postprocess_ms:.2f},"
            f"{baseline_dur_s:.3f},{optimized_dur_s:.3f},{baseline_wer:.4f},{optimized_wer:.4f},{wer_delta:.4f}"
        )

    if worst_delta > args.max_wer_delta:
        raise SystemExit(
            f"WER regression guard failed: worst delta {worst_delta:.4f} > allowed {args.max_wer_delta:.4f}"
        )

    print(f"WER guard passed: worst_delta={worst_delta:.4f} <= {args.max_wer_delta:.4f}")


if __name__ == "__main__":
    main()
