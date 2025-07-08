import os
from PIL import Image
from transformers import pipeline

def load_image():
    """Load the local chrome icon image"""
    image_path = "static/img/android-chrome-512x512.png"
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
    return Image.open(image_path)

def main():
    """Run a simple caption generation using the Gemma model."""
    model_id = "google/gemma-3n-e4b-it"
    pipe = pipeline(
        "image-text-to-text",
        model=model_id,
        device=0 if torch.cuda.is_available() else -1,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else None,
    )

    # Load and process image
    print("Loading local image...")
    image = load_image()
    
    questions = [
        "Describe this image.",
        "What colors are prominent in this image?",
        "Is this an icon or logo? If so, describe its design.",
    ]

    print("\nAsking questions about the image:")
    for question in questions:
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": question},
                ],
            },
        ]
        answer = pipe(text=messages, max_new_tokens=100)[0]["generated_text"][-1]["content"]
        print(f"\nQ: {question}\nA: {answer}")

if __name__ == "__main__":
    main()
