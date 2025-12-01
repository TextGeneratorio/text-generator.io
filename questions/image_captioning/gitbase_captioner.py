"""
GitBase image captioning module with performance optimizations.
Replaces Moondream with Microsoft's GIT-base model for improved speed and accuracy.
"""

import logging
import time
from typing import Dict, Tuple

import torch
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor

from questions.inference_server.model_cache import ModelCache
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class GitBaseCaptioner:
    """
    High-performance GitBase image captioning with multiple optimization techniques.
    """

    def __init__(
        self,
        model_name: str = "microsoft/git-base",
        dtype: torch.dtype = torch.float16,
        device: str = "cuda",
        use_compile: bool = True,
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

    def _load_model(self) -> Tuple[AutoProcessor, AutoModelForVision2Seq]:
        """Load and optimize the GitBase model."""
        logger.info(f"Loading GitBase model: {self.model_name}")

        # Load processor and model
        processor = AutoProcessor.from_pretrained(self.model_name)
        model = AutoModelForVision2Seq.from_pretrained(self.model_name, torch_dtype=self.dtype).to(self.device)

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
    dtype: torch.dtype = torch.float16, use_compile: bool = True, use_channels_last: bool = True
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
    cache_key = f"gitbase_{dtype}_{use_compile}_{use_channels_last}"

    def create_captioner():
        return GitBaseCaptioner(dtype=dtype, use_compile=use_compile, use_channels_last=use_channels_last)

    return _GITBASE_CACHE.add_or_get(cache_key, create_captioner)


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

    # Get captioner
    captioner = get_gitbase_captioner()

    # Generate caption
    if fast_mode:
        return captioner.caption_image_fast(image)
    else:
        return captioner.caption_image_quality(image)
