import argparse
from PIL import Image
from transformers import pipeline
import os


def main():
    parser = argparse.ArgumentParser(description="Generate captions using Gemma")
    parser.add_argument("image", help="Path to image")
    parser.add_argument("prompt", nargs="?", default="Describe this image.", help="Prompt for the model")
    args = parser.parse_args()

    model_id = os.getenv("GEMMA_MODEL_ID", "google/gemma-3n-e4b-it")
    device_env = os.getenv("GEMMA_DEVICE")
    if device_env is not None:
        device = int(device_env)
    else:
        try:
            import torch
            device = 0 if torch.cuda.is_available() else -1
        except ModuleNotFoundError:
            device = -1

    pipe = pipeline("image-text-to-text", model=model_id, device=device)

    img = Image.open(args.image)
    messages = [
        {"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": args.prompt}]},
    ]
    output = pipe(text=messages, max_new_tokens=100)
    print(output[0]["generated_text"][-1]["content"])


if __name__ == "__main__":
    main()
