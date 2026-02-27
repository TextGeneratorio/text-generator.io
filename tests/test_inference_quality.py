#!/usr/bin/env python3
"""
Test inference server endpoints and compare quality before/after optimizations.

Tests:
1. Kokoro TTS - audio quality with perceptual metrics
2. Text generation - output consistency
3. Embeddings - vector similarity/consistency
"""
import os
import sys
import time

import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch


def test_kokoro_tts_quality():
    """Test Kokoro TTS generation and quality."""
    print("\n" + "=" * 60)
    print("Testing Kokoro TTS")
    print("=" * 60)

    from questions.inference_server.kokoro import compile_model, generate_full
    from questions.inference_server.models import build_model

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # Load model
    print("Loading Kokoro model...")
    model = build_model("models/kokoro-v0_19.pth", device)

    # Load voice packs
    voice_names = ["af_nicole", "af_heart", "am_adam"]
    voicepacks = {}
    for name in voice_names:
        try:
            voicepacks[name] = torch.load(
                f"models/voices/{name}.pt", weights_only=True
            ).to(device)
        except FileNotFoundError:
            print(f"  Voice {name} not found, skipping")

    if not voicepacks:
        print("No voice packs found, skipping TTS test")
        return True

    voice_name = list(voicepacks.keys())[0]
    voicepack = voicepacks[voice_name]
    print(f"Using voice: {voice_name}")

    test_texts = [
        "Hello, this is a test of the text to speech system.",
        "The quick brown fox jumps over the lazy dog.",
        "Testing numbers: 1, 2, 3, 4, 5. And prices like $19.99.",
    ]

    results = {"uncompiled": [], "compiled": []}

    # Test uncompiled
    print("\n--- Testing UNCOMPILED model ---")
    model.eval()

    for i, text in enumerate(test_texts):
        torch.cuda.synchronize() if device == "cuda" else None
        start = time.perf_counter()

        audio, phonemes = generate_full(model, text, voicepack, lang=voice_name[0], speed=1.0)

        torch.cuda.synchronize() if device == "cuda" else None
        elapsed = time.perf_counter() - start

        audio_duration = len(audio) / 24000  # 24kHz sample rate
        rtf = elapsed / audio_duration if audio_duration > 0 else 0

        results["uncompiled"].append({
            "text": text[:50],
            "audio_samples": len(audio),
            "audio_duration": audio_duration,
            "inference_time": elapsed,
            "rtf": rtf,
            "audio_stats": {
                "mean": float(np.mean(audio)),
                "std": float(np.std(audio)),
                "min": float(np.min(audio)),
                "max": float(np.max(audio)),
            }
        })
        print(f"  [{i+1}] Time: {elapsed:.3f}s, RTF: {rtf:.2f}x, Duration: {audio_duration:.2f}s")

    # Test compiled (if CUDA available)
    if device == "cuda":
        print("\n--- Testing COMPILED model ---")
        print("Compiling model components...")
        model = compile_model(model, mode="reduce-overhead")

        # Warmup
        print("Warmup...")
        for _ in range(2):
            audio, _ = generate_full(model, "warmup test", voicepack, lang=voice_name[0])

        for i, text in enumerate(test_texts):
            torch.cuda.synchronize()
            start = time.perf_counter()

            audio, phonemes = generate_full(model, text, voicepack, lang=voice_name[0], speed=1.0)

            torch.cuda.synchronize()
            elapsed = time.perf_counter() - start

            audio_duration = len(audio) / 24000
            rtf = elapsed / audio_duration if audio_duration > 0 else 0

            results["compiled"].append({
                "text": text[:50],
                "audio_samples": len(audio),
                "audio_duration": audio_duration,
                "inference_time": elapsed,
                "rtf": rtf,
                "audio_stats": {
                    "mean": float(np.mean(audio)),
                    "std": float(np.std(audio)),
                    "min": float(np.min(audio)),
                    "max": float(np.max(audio)),
                }
            })
            print(f"  [{i+1}] Time: {elapsed:.3f}s, RTF: {rtf:.2f}x, Duration: {audio_duration:.2f}s")

    # Compare results
    print("\n--- Quality Comparison ---")
    if results["compiled"]:
        for i in range(len(test_texts)):
            unc = results["uncompiled"][i]
            comp = results["compiled"][i]

            speedup = unc["inference_time"] / comp["inference_time"]
            sample_diff = abs(unc["audio_samples"] - comp["audio_samples"])

            print(f"  Test {i+1}:")
            print(f"    Speedup: {speedup:.2f}x")
            print(f"    Sample count diff: {sample_diff}")
            print(f"    Uncompiled stats: mean={unc['audio_stats']['mean']:.4f}, std={unc['audio_stats']['std']:.4f}")
            print(f"    Compiled stats: mean={comp['audio_stats']['mean']:.4f}, std={comp['audio_stats']['std']:.4f}")

    print("\n✓ Kokoro TTS test complete")
    return True


def test_text_generation():
    """Test text generation quality and consistency."""
    print("\n" + "=" * 60)
    print("Testing Text Generation")
    print("=" * 60)

    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import fast_inference

    model_cache = ModelCache()

    test_prompts = [
        "The quick brown fox",
        "Once upon a time",
        "In a world where",
    ]

    print("Testing text generation...")
    for prompt in test_prompts:
        params = GenerateParams(
            text=prompt,
            max_length=30,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
        )

        start = time.perf_counter()
        result = fast_inference(generate_params=params, model_cache=model_cache)
        elapsed = time.perf_counter() - start

        if result:
            generated = result[0].get("generated_text", "")[:80]
            print(f"  Prompt: '{prompt}'")
            print(f"  Output: '{generated}...'")
            print(f"  Time: {elapsed:.3f}s")
            print()

    print("✓ Text generation test complete")
    return True


def test_embeddings():
    """Test embedding extraction quality and consistency."""
    print("\n" + "=" * 60)
    print("Testing Embeddings")
    print("=" * 60)

    from questions.inference_server.model_cache import ModelCache
    from questions.models import FeatureExtractParams
    from questions.text_generator_inference import fast_feature_extract_inference

    model_cache = ModelCache()

    test_sentences = [
        "The cat sat on the mat.",
        "The cat sat on the mat.",  # Same sentence for consistency check
        "A dog runs in the park.",  # Different sentence
    ]

    embeddings = []
    print("Extracting embeddings...")

    for sent in test_sentences:
        params = FeatureExtractParams(text=sent, num_features=768)

        start = time.perf_counter()
        result = fast_feature_extract_inference(feature_extract_params=params, model_cache=model_cache)
        elapsed = time.perf_counter() - start

        emb = np.array(result)
        embeddings.append(emb)
        print(f"  '{sent[:40]}...' -> shape={emb.shape}, time={elapsed:.3f}s")

    # Check consistency
    print("\n--- Consistency Check ---")

    # Same sentences should have identical embeddings
    if len(embeddings) >= 2:
        cos_sim_same = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        print(f"  Same sentence cosine similarity: {cos_sim_same:.6f}")

        if cos_sim_same > 0.9999:
            print("  ✓ Identical sentences produce consistent embeddings")
        else:
            print("  ⚠ Warning: Same sentences have different embeddings!")

    # Different sentences should have lower similarity
    if len(embeddings) >= 3:
        cos_sim_diff = np.dot(embeddings[0], embeddings[2]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[2])
        )
        print(f"  Different sentence cosine similarity: {cos_sim_diff:.6f}")

        if cos_sim_diff < cos_sim_same:
            print("  ✓ Different sentences have lower similarity (as expected)")

    print("\n✓ Embeddings test complete")
    return True


def test_audio_perceptual_quality():
    """Test audio quality using perceptual metrics (if available)."""
    print("\n" + "=" * 60)
    print("Testing Audio Perceptual Quality")
    print("=" * 60)

    try:
        import scipy.io.wavfile as wavfile
        from scipy import signal
    except ImportError:
        print("scipy not available, skipping perceptual tests")
        return True

    from questions.inference_server.kokoro import generate_full
    from questions.inference_server.models import build_model

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load model
    model = build_model("models/kokoro-v0_19.pth", device)

    # Load a voice
    try:
        voicepack = torch.load("models/voices/af_nicole.pt", weights_only=True).to(device)
    except FileNotFoundError:
        print("Voice pack not found, skipping perceptual test")
        return True

    test_text = "Hello, this is a test of audio quality."

    # Generate multiple times and check consistency
    print("Generating audio samples for consistency check...")
    samples = []
    for i in range(3):
        audio, _ = generate_full(model, test_text, voicepack, lang="a", speed=1.0)
        samples.append(audio)
        print(f"  Sample {i+1}: {len(audio)} samples, mean={np.mean(audio):.4f}, std={np.std(audio):.4f}")

    # Check audio properties
    print("\n--- Audio Quality Metrics ---")
    for i, audio in enumerate(samples):
        # Check for clipping
        clip_ratio = np.mean(np.abs(audio) > 0.99)

        # Check for silence
        silence_ratio = np.mean(np.abs(audio) < 0.01)

        # Compute spectral properties
        if len(audio) > 1024:
            f, psd = signal.welch(audio, fs=24000, nperseg=1024)
            spectral_centroid = np.sum(f * psd) / np.sum(psd)
        else:
            spectral_centroid = 0

        print(f"  Sample {i+1}:")
        print(f"    Clipping ratio: {clip_ratio:.4%}")
        print(f"    Silence ratio: {silence_ratio:.4%}")
        print(f"    Spectral centroid: {spectral_centroid:.1f} Hz")

        if clip_ratio > 0.01:
            print("    ⚠ Warning: High clipping detected!")
        if silence_ratio > 0.5:
            print("    ⚠ Warning: High silence ratio!")

    # Cross-correlation between samples (should be very high for same input)
    if len(samples) >= 2:
        # Normalize and compare
        s1 = samples[0] / (np.max(np.abs(samples[0])) + 1e-8)
        s2 = samples[1] / (np.max(np.abs(samples[1])) + 1e-8)

        if len(s1) == len(s2):
            correlation = np.corrcoef(s1, s2)[0, 1]
            print(f"\n  Cross-sample correlation: {correlation:.6f}")

            if correlation > 0.99:
                print("  ✓ Audio generation is deterministic")
            else:
                print("  ⚠ Audio varies between runs (may be expected with sampling)")

    print("\n✓ Audio perceptual quality test complete")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Inference Server Quality Tests")
    print("=" * 60)
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")

    all_passed = True

    # Test 1: Kokoro TTS
    try:
        test_kokoro_tts_quality()
    except Exception as e:
        print(f"✗ Kokoro TTS test failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Test 2: Text Generation
    try:
        test_text_generation()
    except Exception as e:
        print(f"✗ Text generation test failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Test 3: Embeddings
    try:
        test_embeddings()
    except Exception as e:
        print(f"✗ Embeddings test failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Test 4: Audio Perceptual Quality
    try:
        test_audio_perceptual_quality()
    except Exception as e:
        print(f"✗ Audio perceptual test failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests completed successfully!")
    else:
        print("Some tests failed - check output above")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
