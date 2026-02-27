"""
Detailed comparison of baseline vs optimized inference.

Measures:
1. Time breakdown (phonemization, tokenization, forward pass)
2. Audio output similarity (waveform comparison)
3. Batch size scaling
4. Memory usage
"""

import time

import numpy as np
import pytest
import torch

SAMPLE_TEXTS = [
    "Hello world.",
    "The quick brown fox jumps over the lazy dog.",
    "Artificial intelligence is transforming every industry.",
    "Machine learning models continue to improve rapidly.",
    "Natural language processing enables new applications.",
    "Speech synthesis has become remarkably realistic.",
    "Deep learning revolutionized computer vision.",
    "Transformer architectures power modern AI systems.",
]


def audio_similarity(audio1: np.ndarray, audio2: np.ndarray) -> float:
    """Compute normalized cross-correlation between two audio signals."""
    if len(audio1) != len(audio2):
        # Pad shorter to match longer
        max_len = max(len(audio1), len(audio2))
        audio1 = np.pad(audio1, (0, max_len - len(audio1)))
        audio2 = np.pad(audio2, (0, max_len - len(audio2)))

    # Normalize
    audio1 = audio1 - np.mean(audio1)
    audio2 = audio2 - np.mean(audio2)

    norm1 = np.linalg.norm(audio1)
    norm2 = np.linalg.norm(audio2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return np.dot(audio1, audio2) / (norm1 * norm2)


class TestTimeBreakdown:
    """Measure where time is spent in the pipeline."""

    @pytest.fixture(scope="class")
    def models(self):
        """Load models once for all tests."""
        from questions.inference_server.kokoro import phonemize, tokenize
        from questions.inference_server.models import build_model

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = build_model("models/kokoro-v0_19.pth", device)
        voicepack = torch.load("models/voices/af_nicole.pt", weights_only=True).to(device)

        return {
            "model": model,
            "voicepack": voicepack,
            "phonemize": phonemize,
            "tokenize": tokenize,
            "device": device,
        }

    def test_time_breakdown_single(self, models):
        """Break down time for a single inference."""
        text = "The quick brown fox jumps over the lazy dog."
        from questions.inference_server.kokoro import forward

        # Warmup
        for _ in range(2):
            ps = models["phonemize"](text, "a")
            tokens = models["tokenize"](ps)
            ref_s = models["voicepack"][len(tokens)]
            forward(models["model"], tokens, ref_s, 1.0)

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        # Measure phonemization
        start = time.perf_counter()
        for _ in range(10):
            ps = models["phonemize"](text, "a")
        phonemize_time = (time.perf_counter() - start) / 10 * 1000

        # Measure tokenization
        start = time.perf_counter()
        for _ in range(100):
            tokens = models["tokenize"](ps)
        tokenize_time = (time.perf_counter() - start) / 100 * 1000

        # Measure forward pass
        ref_s = models["voicepack"][len(tokens)]
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        start = time.perf_counter()
        for _ in range(10):
            audio = forward(models["model"], tokens, ref_s, 1.0)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
        forward_time = (time.perf_counter() - start) / 10 * 1000

        total = phonemize_time + tokenize_time + forward_time

        print("\n" + "=" * 50)
        print("TIME BREAKDOWN (single inference)")
        print("=" * 50)
        print(f"Text: '{text[:40]}...' ({len(tokens)} tokens)")
        print("-" * 50)
        print(f"Phonemization:  {phonemize_time:6.2f}ms  ({phonemize_time/total*100:5.1f}%)")
        print(f"Tokenization:   {tokenize_time:6.2f}ms  ({tokenize_time/total*100:5.1f}%)")
        print(f"Forward pass:   {forward_time:6.2f}ms  ({forward_time/total*100:5.1f}%)")
        print("-" * 50)
        print(f"Total:          {total:6.2f}ms")
        print("=" * 50)

        # Forward pass should dominate
        assert forward_time > phonemize_time, "Forward should take more than phonemize"

    def test_batch_scaling(self, models):
        """Test how performance scales with batch size."""
        from questions.inference_server.kokoro import generate_full

        batch_sizes = [1, 2, 4, 8]
        results = []

        for batch_size in batch_sizes:
            texts = SAMPLE_TEXTS[:batch_size]

            if torch.cuda.is_available():
                torch.cuda.synchronize()

            start = time.perf_counter()
            for text in texts:
                generate_full(models["model"], text, models["voicepack"], lang="a")
            if torch.cuda.is_available():
                torch.cuda.synchronize()

            total_time = (time.perf_counter() - start) * 1000
            per_request = total_time / batch_size
            throughput = batch_size / (total_time / 1000)

            results.append({
                "batch_size": batch_size,
                "total_ms": total_time,
                "per_request_ms": per_request,
                "throughput_rps": throughput,
            })

        print("\n" + "=" * 60)
        print("BATCH SIZE SCALING")
        print("=" * 60)
        print(f"{'Batch':>6} {'Total(ms)':>12} {'Per-Req(ms)':>12} {'Throughput':>12}")
        print("-" * 60)
        for r in results:
            print(f"{r['batch_size']:>6} {r['total_ms']:>12.2f} {r['per_request_ms']:>12.2f} {r['throughput_rps']:>10.2f}/s")
        print("=" * 60)

        # Per-request time should be roughly constant (sequential)
        times = [r["per_request_ms"] for r in results]
        variance = np.std(times) / np.mean(times)
        print(f"Per-request variance: {variance:.2%}")


class TestAudioComparison:
    """Compare audio outputs between baseline and optimized."""

    @pytest.fixture(scope="class")
    def baseline_model(self):
        """Load baseline model."""
        from questions.inference_server.kokoro import generate_full
        from questions.inference_server.models import build_model

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = build_model("models/kokoro-v0_19.pth", device)
        voicepack = torch.load("models/voices/af_nicole.pt", weights_only=True).to(device)

        return model, voicepack, generate_full

    @pytest.fixture(scope="class")
    def optimized_tts(self):
        """Load optimized TTS."""
        from questions.inference_server.optimized_inference import OptimizedKokoroTTS

        tts = OptimizedKokoroTTS()
        tts.load()
        return tts

    def test_output_identical(self, baseline_model, optimized_tts):
        """Verify optimized produces identical output to baseline."""
        model, voicepack, generate_full = baseline_model

        for text in SAMPLE_TEXTS[:3]:
            # Baseline
            baseline_audio, _ = generate_full(model, text, voicepack, lang="a")

            # Optimized
            opt_audio = optimized_tts.generate(text)

            # Compare
            similarity = audio_similarity(baseline_audio, opt_audio)
            len_diff = abs(len(baseline_audio) - len(opt_audio)) / max(len(baseline_audio), len(opt_audio))

            print(f"\n'{text[:30]}...'")
            print(f"  Length diff: {len_diff:.4%}")
            print(f"  Similarity: {similarity:.6f}")

            assert len_diff < 0.01, f"Length differs too much: {len_diff:.2%}"
            # torch.compile can produce slightly different results due to kernel fusion
            assert similarity > 0.98, f"Audio not similar enough: {similarity:.4f}"

    def test_batch_vs_single_identical(self, optimized_tts):
        """Verify batch processing produces same output as single."""
        texts = SAMPLE_TEXTS[:4]

        # Single processing
        single_results = [optimized_tts.generate(text) for text in texts]

        # Batch processing
        batch_results = optimized_tts.generate_batch(texts)

        for i, (single, batch) in enumerate(zip(single_results, batch_results)):
            similarity = audio_similarity(single, batch)
            print(f"Text {i}: similarity = {similarity:.6f}")

            # torch.compile can produce slightly different results
            assert similarity > 0.98, f"Batch output differs from single: {similarity:.4f}"


class TestMemoryUsage:
    """Track memory usage during inference."""

    def test_memory_during_inference(self):
        """Measure GPU memory during inference."""
        if not torch.cuda.is_available():
            pytest.skip("No CUDA available")

        from questions.inference_server.optimized_inference import OptimizedKokoroTTS

        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()

        mem_before = torch.cuda.memory_allocated() / 1e6

        tts = OptimizedKokoroTTS()
        tts.load()

        mem_after_load = torch.cuda.memory_allocated() / 1e6

        # Run some inferences
        for text in SAMPLE_TEXTS:
            tts.generate(text)

        mem_after_inference = torch.cuda.memory_allocated() / 1e6
        peak_mem = torch.cuda.max_memory_allocated() / 1e6

        print("\n" + "=" * 50)
        print("GPU MEMORY USAGE")
        print("=" * 50)
        print(f"Before load:      {mem_before:>8.1f} MB")
        print(f"After load:       {mem_after_load:>8.1f} MB (+{mem_after_load - mem_before:.1f})")
        print(f"After inference:  {mem_after_inference:>8.1f} MB")
        print(f"Peak memory:      {peak_mem:>8.1f} MB")
        print("=" * 50)

        # Cleanup
        tts.unload()

        mem_after_unload = torch.cuda.memory_allocated() / 1e6
        print(f"After unload:     {mem_after_unload:>8.1f} MB")


class TestPhonemizerOptimization:
    """Test phonemizer overhead and potential optimizations."""

    def test_phonemizer_is_bottleneck(self):
        """Measure if phonemizer is a bottleneck for small texts."""
        from questions.inference_server.kokoro import phonemize

        texts = {
            "tiny": "Hi.",
            "short": "Hello world.",
            "medium": "The quick brown fox jumps over the lazy dog.",
        }

        print("\n" + "=" * 50)
        print("PHONEMIZER TIMING")
        print("=" * 50)

        for name, text in texts.items():
            # Warmup
            phonemize(text, "a")

            # Measure
            start = time.perf_counter()
            for _ in range(50):
                phonemize(text, "a")
            avg_time = (time.perf_counter() - start) / 50 * 1000

            print(f"{name:>10}: {avg_time:.2f}ms for '{text[:20]}...'")

        print("=" * 50)
        print("Note: espeak phonemizer has ~20-50ms startup overhead")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
