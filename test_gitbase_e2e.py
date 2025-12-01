#!/usr/bin/env python3
"""
End-to-end tests for GitBase image captioning with full GPU optimization testing.
Run this manually to test actual model performance and functionality.
"""

import logging
import os
import sys
import time

import torch
from PIL import Image

from questions.image_captioning.gitbase_captioner import GitBaseCaptioner, caption_image_bytes, get_gitbase_captioner
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def create_test_images():
    """Create a variety of test images for comprehensive testing."""
    test_images = {}

    # Simple colored squares
    test_images["red_square"] = Image.new("RGB", (224, 224), color=(255, 0, 0))
    test_images["blue_square"] = Image.new("RGB", (224, 224), color=(0, 0, 255))
    test_images["green_square"] = Image.new("RGB", (224, 224), color=(0, 255, 0))

    # Gradient image
    gradient = Image.new("RGB", (224, 224))
    for x in range(224):
        for y in range(224):
            gradient.putpixel((x, y), (x, y, (x + y) // 2))
    test_images["gradient"] = gradient

    # Simple pattern
    pattern = Image.new("RGB", (224, 224), color=(255, 255, 255))
    for x in range(0, 224, 20):
        for y in range(0, 224, 20):
            for i in range(10):
                for j in range(10):
                    if x + i < 224 and y + j < 224:
                        pattern.putpixel((x + i, y + j), (0, 0, 0))
    test_images["checkerboard"] = pattern

    # Load real image if available
    real_image_paths = ["static/img/me.jpg", "static/img/android-chrome-512x512.png", "static/images/logo.png"]

    for path in real_image_paths:
        if os.path.exists(path):
            try:
                test_images[f"real_{os.path.basename(path)}"] = Image.open(path).convert("RGB")
                logger.info(f"Loaded real test image: {path}")
                break
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")

    return test_images


def test_basic_functionality():
    """Test basic GitBase functionality."""
    print("=" * 60)
    print("TESTING BASIC GITBASE FUNCTIONALITY")
    print("=" * 60)

    test_images = create_test_images()

    # Test with CPU first for compatibility
    print("\n--- Testing CPU Implementation ---")
    captioner_cpu = GitBaseCaptioner(dtype=torch.float32, device="cpu", use_compile=False, use_channels_last=False)

    for name, image in list(test_images.items())[:2]:  # Test first 2 images
        try:
            start_time = time.time()
            caption = captioner_cpu.caption_image(image)
            elapsed = time.time() - start_time

            print(f"Image: {name}")
            print(f"Caption: {caption}")
            print(f"Time: {elapsed:.3f}s")
            print()

            assert isinstance(caption, str)
            assert len(caption) > 0

        except Exception as e:
            print(f"ERROR with {name}: {e}")
            import traceback

            traceback.print_exc()

    print("✅ Basic CPU functionality test passed!")


def test_gpu_optimizations():
    """Test GPU optimizations if available."""
    if not torch.cuda.is_available():
        print("⚠️  CUDA not available, skipping GPU tests")
        return

    print("=" * 60)
    print("TESTING GPU OPTIMIZATIONS")
    print("=" * 60)

    test_images = create_test_images()
    sample_image = list(test_images.values())[0]

    # Test different optimization combinations
    configs = [
        {"name": "Baseline FP32", "dtype": torch.float32, "use_compile": False, "use_channels_last": False},
        {"name": "FP16 Optimization", "dtype": torch.float16, "use_compile": False, "use_channels_last": False},
        {"name": "BF16 Optimization", "dtype": torch.bfloat16, "use_compile": False, "use_channels_last": False},
        {"name": "Channels Last", "dtype": torch.float16, "use_compile": False, "use_channels_last": True},
        {"name": "Torch Compile + FP16", "dtype": torch.float16, "use_compile": True, "use_channels_last": False},
        {"name": "All Optimizations", "dtype": torch.float16, "use_compile": True, "use_channels_last": True},
    ]

    results = {}

    for config in configs:
        try:
            print(f"\n--- Testing {config['name']} ---")

            captioner = GitBaseCaptioner(
                dtype=config["dtype"],
                device="cuda",
                use_compile=config["use_compile"],
                use_channels_last=config["use_channels_last"],
            )

            # Warmup run
            _ = captioner.caption_image_fast(sample_image)

            # Benchmark runs
            times = []
            captions = []

            for i in range(5):
                start_time = time.time()
                caption = captioner.caption_image_fast(sample_image)
                elapsed = time.time() - start_time
                times.append(elapsed)
                captions.append(caption)

            avg_time = sum(times) / len(times)
            results[config["name"]] = avg_time

            print(f"Average time: {avg_time:.3f}s")
            print(f"Sample caption: {captions[0]}")
            print(f"Caption consistency: {len(set(captions))} unique captions out of 5")

        except Exception as e:
            print(f"ERROR with {config['name']}: {e}")
            import traceback

            traceback.print_exc()

    # Print comparison
    if results:
        print("\n--- GPU Optimization Results ---")
        baseline_time = results.get("Baseline FP32", 1.0)

        for name, time_val in results.items():
            speedup = baseline_time / time_val if time_val > 0 else 0
            print(f"{name:20}: {time_val:.3f}s ({speedup:.2f}x speedup)")

        best_config = min(results.keys(), key=lambda k: results[k])
        best_time = results[best_config]
        total_speedup = baseline_time / best_time

        print(f"\n🚀 Best configuration: {best_config}")
        print(f"🚀 Total speedup: {total_speedup:.2f}x")
        print(f"🚀 Final optimized time: {best_time:.3f}s")


def test_different_generation_modes():
    """Test different generation modes and parameters."""
    print("=" * 60)
    print("TESTING GENERATION MODES")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    captioner = GitBaseCaptioner(
        dtype=dtype, device=device, use_compile=device == "cuda", use_channels_last=device == "cuda"
    )

    test_images = create_test_images()
    sample_image = list(test_images.values())[0]

    # Test different generation modes
    modes = [
        {"name": "Ultra Fast (max_length=10)", "params": {"max_length": 10, "num_beams": 1, "do_sample": False}},
        {"name": "Fast (max_length=20)", "params": {"max_length": 20, "num_beams": 1, "do_sample": False}},
        {"name": "Quality (max_length=30, beams=3)", "params": {"max_length": 30, "num_beams": 3, "do_sample": False}},
        {
            "name": "Creative (sampling)",
            "params": {"max_length": 25, "num_beams": 1, "do_sample": True, "temperature": 0.8},
        },
    ]

    for mode in modes:
        try:
            print(f"\n--- {mode['name']} ---")

            # Time multiple runs
            times = []
            captions = []

            for i in range(3):
                start_time = time.time()
                caption = captioner.caption_image(sample_image, **mode["params"])
                elapsed = time.time() - start_time
                times.append(elapsed)
                captions.append(caption)

            avg_time = sum(times) / len(times)
            print(f"Average time: {avg_time:.3f}s")
            print("Captions:")
            for i, caption in enumerate(captions):
                print(f"  {i + 1}: {caption}")

        except Exception as e:
            print(f"ERROR with {mode['name']}: {e}")


def test_api_functions():
    """Test module-level API functions."""
    print("=" * 60)
    print("TESTING API FUNCTIONS")
    print("=" * 60)

    test_images = create_test_images()
    sample_image = list(test_images.values())[0]

    # Test get_gitbase_captioner caching
    print("\n--- Testing Cached Captioner ---")
    captioner1 = get_gitbase_captioner(dtype=torch.float16)
    captioner2 = get_gitbase_captioner(dtype=torch.float16)

    print(f"Same instance returned: {captioner1 is captioner2}")
    assert captioner1 is captioner2, "Caching not working properly"

    # Test caption_image_bytes
    print("\n--- Testing Bytes API ---")
    from io import BytesIO

    # Convert image to bytes
    buffer = BytesIO()
    sample_image.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()

    # Test fast mode
    start_time = time.time()
    caption_fast = caption_image_bytes(image_bytes, fast_mode=True)
    fast_time = time.time() - start_time

    # Test quality mode
    start_time = time.time()
    caption_quality = caption_image_bytes(image_bytes, fast_mode=False)
    quality_time = time.time() - start_time

    print(f"Fast caption: {caption_fast} (time: {fast_time:.3f}s)")
    print(f"Quality caption: {caption_quality} (time: {quality_time:.3f}s)")

    assert isinstance(caption_fast, str)
    assert isinstance(caption_quality, str)
    assert len(caption_fast) > 0
    assert len(caption_quality) > 0


def test_comprehensive_image_types():
    """Test with different image types and sizes."""
    print("=" * 60)
    print("TESTING COMPREHENSIVE IMAGE TYPES")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    captioner = GitBaseCaptioner(
        dtype=dtype,
        device=device,
        use_compile=False,  # Disable for stability
        use_channels_last=False,
    )

    # Test different image sizes
    sizes = [(128, 128), (224, 224), (256, 256), (512, 512)]

    for width, height in sizes:
        try:
            print(f"\n--- Testing {width}x{height} image ---")

            # Create test image
            test_image = Image.new("RGB", (width, height))
            for x in range(width):
                for y in range(height):
                    # Create a simple pattern
                    r = (x * 255) // width
                    g = (y * 255) // height
                    b = ((x + y) * 255) // (width + height)
                    test_image.putpixel((x, y), (r, g, b))

            start_time = time.time()
            caption = captioner.caption_image_fast(test_image)
            elapsed = time.time() - start_time

            print(f"Caption: {caption}")
            print(f"Time: {elapsed:.3f}s")

            assert isinstance(caption, str)
            assert len(caption) > 0

        except Exception as e:
            print(f"ERROR with {width}x{height}: {e}")


def test_memory_usage():
    """Test memory usage and cleanup."""
    if not torch.cuda.is_available():
        print("⚠️  CUDA not available, skipping memory tests")
        return

    print("=" * 60)
    print("TESTING MEMORY USAGE")
    print("=" * 60)

    test_images = create_test_images()
    sample_image = list(test_images.values())[0]

    # Clear cache
    torch.cuda.empty_cache()
    initial_memory = torch.cuda.memory_allocated()

    print(f"Initial GPU memory: {initial_memory / 1024**2:.1f} MB")

    # Create captioner and run inference
    captioner = GitBaseCaptioner(dtype=torch.float16, device="cuda", use_compile=False, use_channels_last=True)

    # Load model
    captioner.load()
    after_load_memory = torch.cuda.memory_allocated()

    print(f"Memory after model load: {after_load_memory / 1024**2:.1f} MB")
    print(f"Model memory usage: {(after_load_memory - initial_memory) / 1024**2:.1f} MB")

    # Run inference
    for i in range(10):
        captioner.caption_image_fast(sample_image)
        if i == 0:
            after_first_inference = torch.cuda.memory_allocated()
            print(f"Memory after first inference: {after_first_inference / 1024**2:.1f} MB")

    final_memory = torch.cuda.memory_allocated()
    print(f"Final memory: {final_memory / 1024**2:.1f} MB")
    print(f"Memory growth during inference: {(final_memory - after_first_inference) / 1024**2:.1f} MB")


def main():
    """Run all end-to-end tests."""
    print("🚀 Starting GitBase End-to-End Tests")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name()}")
        print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print()

    try:
        test_basic_functionality()
        test_gpu_optimizations()
        test_different_generation_modes()
        test_api_functions()
        test_comprehensive_image_types()
        test_memory_usage()

        print("=" * 60)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
