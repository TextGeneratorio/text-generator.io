"""
GitBase image captioning module with performance optimizations.
Replaces Moondream with Microsoft's GIT-base model for improved speed and accuracy.
"""

import gc
import logging
import os
import time
from typing import Dict, Tuple

import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

from questions.inference_server.model_cache import ModelCache
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

GITBASE_MIN_FREE_VRAM_GB = float(os.getenv("GITBASE_MIN_FREE_VRAM_GB", "1.0"))


def _cuda_free_vram_gb() -> float:
    if not torch.cuda.is_available():
        return 0.0
    try:
        free_bytes, _ = torch.cuda.mem_get_info(0)
        return free_bytes / (1024**3)
    except Exception as e:
        logger.debug("Unable to read CUDA free memory: %s", e)
        return 0.0


def _select_caption_device() -> str:
    if not torch.cuda.is_available():
        return "cpu"

    free_gb = _cuda_free_vram_gb()
    if free_gb < GITBASE_MIN_FREE_VRAM_GB:
        logger.warning(
            "Using CPU for GitBase captioning: %.2fGB free VRAM below %.2fGB threshold",
            free_gb,
            GITBASE_MIN_FREE_VRAM_GB,
        )
        return "cpu"

    return "cuda"


def _captioner_settings_for_device(device: str) -> tuple[torch.dtype, bool]:
    if device == "cuda":
        return torch.float16, True
    return torch.float32, False


def _clear_cuda_after_oom():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


class GitBaseCaptioner:
    """
    High-performance GitBase image captioning with multiple optimization techniques.
    """

    def __init__(
        self,
        model_name: str = "microsoft/git-base",
        dtype: torch.dtype = torch.float16,
        device: str = "cuda",
        use_compile: bool = False,
        use_channels_last: bool = True,
    ):
        """
        Initialize GitBase captioner with optimizations.

        Args:
            model_name: HuggingFace model identifier
            dtype: Torch dtype for model (float16, bfloat16, or float32)
            device: Device to run model on
            use_compile: Whether to use torch.compile for optimization
            use_channels_last: Whether to use channels_last memory format
        """
        self.model_name = model_name
        self.dtype = dtype
        self.device = device
        self.use_compile = use_compile
        self.use_channels_last = use_channels_last

        self.processor = None
        self.model = None
        self._is_loaded = False
        self._warmup_done = False

    def _load_model(self) -> Tuple[AutoProcessor, AutoModelForImageTextToText]:
        """Load and optimize the GitBase model."""
        logger.info(f"Loading GitBase model: {self.model_name}")

        # Load processor and model
        processor = AutoProcessor.from_pretrained(self.model_name)
        model = AutoModelForImageTextToText.from_pretrained(self.model_name, torch_dtype=self.dtype).to(self.device)

        # Apply memory format optimization
        if self.use_channels_last and self.device == "cuda":
            model = model.to(memory_format=torch.channels_last)
            logger.info("Applied channels_last memory format")

        # Apply torch.compile optimization
        if self.use_compile and torch.__version__ >= "2.0":
            model = torch.compile(model)
            logger.info("Applied torch.compile optimization")

        return processor, model

    def load(self):
        """Load the model if not already loaded."""
        if not self._is_loaded:
            self.processor, self.model = self._load_model()
            self._is_loaded = True
            logger.info("GitBase model loaded successfully")

    def unload(self):
        """Release loaded model resources."""
        try:
            if self.model is not None and hasattr(self.model, "to"):
                self.model.to("cpu")
        except Exception as e:
            logger.debug("GitBase unload cleanup failed: %s", e)

        self.processor = None
        self.model = None
        self._is_loaded = False
        self._warmup_done = False
        _clear_cuda_after_oom()

    def _warmup(self):
        """Warmup the model with a dummy inference to optimize performance."""
        if self._warmup_done:
            return

        logger.info("Warming up GitBase model...")

        # Create a small dummy image for warmup
        dummy_image = Image.new("RGB", (224, 224), color=(128, 128, 128))

        try:
            inputs = self.processor(images=dummy_image, return_tensors="pt").to(self.device)

            # Apply channels_last to inputs if enabled
            if self.use_channels_last:
                inputs = {k: v.to(memory_format=torch.channels_last) if v.dim() == 4 else v for k, v in inputs.items()}

            with torch.inference_mode():
                _ = self.model.generate(**inputs, num_beams=1, max_length=10)

            self._warmup_done = True
            logger.info("GitBase model warmup completed")

        except Exception as e:
            logger.warning(f"Warmup failed: {e}")

    def caption_image(
        self,
        image: Image.Image,
        max_length: int = 20,
        num_beams: int = 1,
        do_sample: bool = False,
        temperature: float = 1.0,
    ) -> str:
        """
        Generate caption for an image using optimized GitBase model.

        Args:
            image: PIL Image to caption
            max_length: Maximum length of generated caption
            num_beams: Number of beams for beam search (1 for greedy)
            do_sample: Whether to use sampling
            temperature: Sampling temperature

        Returns:
            Generated caption as string
        """
        self.load()
        self._warmup()

        # Prepare inputs
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)

        # Apply channels_last to inputs if enabled
        if self.use_channels_last:
            inputs = {k: v.to(memory_format=torch.channels_last) if v.dim() == 4 else v for k, v in inputs.items()}

        # Generate caption
        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=num_beams,
                do_sample=do_sample,
                temperature=temperature if do_sample else 1.0,
            )

        # Decode caption
        caption = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return caption.strip()

    def caption_image_fast(self, image: Image.Image) -> str:
        """
        Generate caption with fastest possible settings.

        Args:
            image: PIL Image to caption

        Returns:
            Generated caption as string
        """
        return self.caption_image(image=image, max_length=10, num_beams=1, do_sample=False)

    def caption_image_quality(self, image: Image.Image) -> str:
        """
        Generate caption with quality-focused settings.

        Args:
            image: PIL Image to caption

        Returns:
            Generated caption as string
        """
        return self.caption_image(image=image, max_length=30, num_beams=3, do_sample=False)

    def benchmark(self, image: Image.Image, num_runs: int = 5) -> Dict[str, float]:
        """
        Benchmark captioning performance.

        Args:
            image: PIL Image to benchmark with
            num_runs: Number of runs for averaging

        Returns:
            Dictionary with timing results
        """
        self.load()
        self._warmup()

        results = {}

        # Benchmark fast mode
        times = []
        for _ in range(num_runs):
            start = time.time()
            _ = self.caption_image_fast(image)
            times.append(time.time() - start)
        results["fast_mode"] = sum(times) / len(times)

        # Benchmark quality mode
        times = []
        for _ in range(num_runs):
            start = time.time()
            _ = self.caption_image_quality(image)
            times.append(time.time() - start)
        results["quality_mode"] = sum(times) / len(times)

        return results


# Global model cache instance
_GITBASE_CACHE = ModelCache()


def get_gitbase_captioner(
    dtype: torch.dtype = torch.float16,
    use_compile: bool = False,
    use_channels_last: bool = True,
    device: str = "cuda",
) -> GitBaseCaptioner:
    """
    Get cached GitBase captioner instance.

    Args:
        dtype: Torch dtype for model
        use_compile: Whether to use torch.compile
        use_channels_last: Whether to use channels_last memory format

    Returns:
        GitBaseCaptioner instance
    """
    cache_key = f"gitbase_{device}_{dtype}_{use_compile}_{use_channels_last}"

    def create_captioner():
        return GitBaseCaptioner(
            dtype=dtype,
            device=device,
            use_compile=use_compile,
            use_channels_last=use_channels_last,
        )

    return _GITBASE_CACHE.add_or_get(cache_key, create_captioner)


def _caption_with_captioner(captioner: GitBaseCaptioner, image: Image.Image, fast_mode: bool) -> str:
    if fast_mode:
        return captioner.caption_image_fast(image)
    return captioner.caption_image_quality(image)


def caption_image_bytes(image_bytes: bytes, prompt: str = "Describe this image.", fast_mode: bool = True) -> str:
    """
    Caption image from bytes - replacement for get_caption_for_image_response.

    Args:
        image_bytes: Raw image bytes
        prompt: Caption prompt (note: GitBase doesn't use prompts like Moondream)
        fast_mode: Whether to use fast captioning mode

    Returns:
        Generated caption
    """
    from io import BytesIO

    # Convert bytes to PIL Image
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    device = _select_caption_device()
    dtype, use_channels_last = _captioner_settings_for_device(device)
    captioner = get_gitbase_captioner(dtype=dtype, use_channels_last=use_channels_last, device=device)

    try:
        return _caption_with_captioner(captioner, image, fast_mode)
    except torch.cuda.OutOfMemoryError:
        if device != "cuda":
            raise
        logger.warning("GitBase CUDA captioning ran out of memory; retrying on CPU")
        captioner.unload()
        cpu_captioner = get_gitbase_captioner(
            dtype=torch.float32,
            use_compile=False,
            use_channels_last=False,
            device="cpu",
        )
        return _caption_with_captioner(cpu_captioner, image, fast_mode)
