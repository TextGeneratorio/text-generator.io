"""
Model cache for GPU-resident models with conservative defaults.
Evicts by LRU when exceeding MAX_CACHED_MODELS and/or under VRAM pressure.
"""

import gc
import logging
import os
from collections import OrderedDict
from typing import Callable, Optional

import torch
import torch.cuda

from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Memory threshold: evict if free VRAM drops below this (in GB)
MIN_FREE_VRAM_GB = float(os.environ.get("MIN_FREE_VRAM_GB", "4.0"))

# Whether to keep all models on GPU (only evict on low VRAM)
KEEP_ALL_ON_GPU = os.environ.get("KEEP_ALL_ON_GPU", "0") == "1"

# Maximum number of cached models (0 = unlimited)
MAX_CACHED_MODELS = int(os.environ.get("MAX_CACHED_MODELS", "3"))


def get_gpu_memory_info():
    """Get GPU memory info in GB."""
    if not torch.cuda.is_available():
        return {"total": 0, "used": 0, "free": 0}

    total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    reserved = torch.cuda.memory_reserved(0) / (1024**3)
    allocated = torch.cuda.memory_allocated(0) / (1024**3)
    free = total - reserved

    return {"total": total, "used": allocated, "reserved": reserved, "free": free}


class ModelCache:
    """
    GPU-resident model cache with LRU eviction.

    Key features:
    - Keeps models on GPU with LRU eviction by default
    - Evicts when free VRAM drops below MIN_FREE_VRAM_GB (if KEEP_ALL_ON_GPU=1)
    - Enforces MAX_CACHED_MODELS when set
    - LRU eviction order when eviction is necessary
    - Fast model switching with no CPU offload
    """

    def __init__(self, max_size_gb: int = 28):
        self.max_size_gb = max_size_gb
        self.cache: OrderedDict[str, any] = OrderedDict()
        self.most_recent_name: Optional[str] = None
        self._log_memory_status()

    def _log_memory_status(self):
        """Log current GPU memory status."""
        if DEVICE == "cuda":
            mem = get_gpu_memory_info()
            logger.info(f"GPU Memory: {mem['used']:.1f}GB used / {mem['total']:.1f}GB total ({mem['free']:.1f}GB free)")

    def __len__(self):
        return len(self.cache)

    def _should_evict_for_memory(self) -> bool:
        """Check if we need to evict models based on memory pressure."""
        if DEVICE != "cuda":
            return False
        mem = get_gpu_memory_info()
        should_evict = mem["free"] < MIN_FREE_VRAM_GB
        if should_evict:
            logger.warning(f"Low VRAM: {mem['free']:.1f}GB free < {MIN_FREE_VRAM_GB}GB threshold")
        return should_evict

    def _should_evict_for_size(self) -> bool:
        """Check if we exceed the max cached models limit."""
        if MAX_CACHED_MODELS <= 0:
            return False
        return len(self.cache) >= MAX_CACHED_MODELS

    def _evict_lru_model(self, exclude_name: Optional[str]) -> bool:
        """Evict the least recently used model (except the excluded one)."""
        for model_name in list(self.cache.keys()):
            if model_name == exclude_name:
                continue

            logger.info(f"Evicting LRU model: {model_name}")
            model = self.cache.pop(model_name)

            try:
                if isinstance(model, (list, tuple)):
                    for m in model:
                        if hasattr(m, 'to'):
                            m.to("cpu")
                        del m
                elif hasattr(model, 'to'):
                    model.to("cpu")
                del model
            except Exception as e:
                logger.debug(f"Eviction cleanup: {e}")

            gc.collect()
            if DEVICE == "cuda":
                torch.cuda.empty_cache()

            self._log_memory_status()
            return True

        return False

    def add_or_get(self, model_name: str, add_model_func: Callable):
        """Get model from cache or load it. Models stay on GPU."""
        self.most_recent_name = model_name

        # If model already cached, move to end (most recently used) and return
        if model_name in self.cache:
            self.cache.move_to_end(model_name)
            logger.info(f"Cache hit: {model_name} (keeping on GPU)")
            return self.cache[model_name]

        # Enforce size limit before loading
        while self._should_evict_for_size() and len(self.cache) > 0:
            if not self._evict_lru_model(model_name):
                break

        # If configured to keep all on GPU, only evict when memory is tight
        if KEEP_ALL_ON_GPU:
            while self._should_evict_for_memory() and len(self.cache) > 0:
                if not self._evict_lru_model(model_name):
                    break

        # Load the new model
        logger.info(f"Loading model: {model_name}")
        try:
            self.cache[model_name] = add_model_func()
            logger.info(f"Loaded model: {model_name}")
            self._log_memory_status()
        except torch.cuda.OutOfMemoryError:
            logger.error(f"OOM loading {model_name}, evicting and retrying...")
            gc.collect()
            torch.cuda.empty_cache()

            # Force evict oldest model and retry
            if self._evict_lru_model(model_name):
                self.cache[model_name] = add_model_func()
                logger.info(f"Loaded model after eviction: {model_name}")
            else:
                raise

        # Post-load memory pressure check (best effort)
        if KEEP_ALL_ON_GPU:
            while self._should_evict_for_memory() and len(self.cache) > 0:
                if not self._evict_lru_model(model_name):
                    break

        return self.cache[model_name]

    def get(self, model_name: str) -> Callable:
        if model_name not in self.cache:
            raise RuntimeError(f"Model {model_name} not found in cache")
        self.cache.move_to_end(model_name)  # Update LRU order
        return self.cache[model_name]

    def list_models(self) -> list:
        """List all cached model names."""
        return list(self.cache.keys())

    def is_loaded(self, model_name: str) -> bool:
        """Check if a model is in cache."""
        return model_name in self.cache

    def empty_all_caches(self):
        """Clear all models from cache."""
        for _ in list(self.cache.keys()):
            self._evict_lru_model(exclude_name=None)
        self.cache.clear()
        gc.collect()
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
        logger.info("Cleared all model caches")
        self._log_memory_status()
