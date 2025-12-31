#!/usr/bin/env python
"""Target script for py-spy profiling."""

import gc
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch


def main():
    from questions.inference_server.model_cache import ModelCache
    from questions.models import GenerateParams
    from questions.text_generator_inference import fast_inference

    model_cache = ModelCache()
    params = GenerateParams(
        text="The future of AI is",
        max_length=30,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        number_of_results=1,
        model="any",
    )

    # Warmup
    print("Warmup...", file=sys.stderr)
    fast_inference(params, model_cache)
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Profile runs
    print("Profiling...", file=sys.stderr)
    for i in range(3):
        result = fast_inference(params, model_cache)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        print(f"Run {i+1}/3 complete", file=sys.stderr)


if __name__ == "__main__":
    main()
