#!/usr/bin/env python
"""Simple CLI for running vLLM inference."""
import argparse
from questions.vllm_inference import vllm_inference, VLLM_AVAILABLE
from questions.models import GenerateParams
from questions.constants import weights_path_tgz


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate text using vLLM")
    parser.add_argument("text", help="prompt text")
    parser.add_argument("--max-length", type=int, default=100)
    args = parser.parse_args()

    params = GenerateParams(text=args.text, max_length=args.max_length)
    if not VLLM_AVAILABLE:
        raise SystemExit("vLLM is not installed")
    result = vllm_inference(params, weights_path_tgz)[0]
    print(result["generated_text"])


if __name__ == "__main__":
    main()
