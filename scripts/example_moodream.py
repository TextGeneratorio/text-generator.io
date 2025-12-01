import os

from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer


def ensure_model_downloaded():
    """Ensure model is downloaded to models directory"""
    model_path = "models/moondream2"
    if not os.path.exists(model_path):
        print(f"Model not found in {model_path}, downloading...")
        os.makedirs(model_path, exist_ok=True)
    return model_path


def load_image():
    """Load the local chrome icon image"""
    image_path = "static/img/android-chrome-512x512.png"
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
    return Image.open(image_path)


def main():
    # Initialize model and tokenizer
    model_id = "vikhyatk/moondream2"
    revision = "2024-08-26"
    model_path = ensure_model_downloaded()

    print("Loading model and tokenizer...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id, trust_remote_code=True, revision=revision, cache_dir=model_path, force_download=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, cache_dir=model_path, force_download=True)

    # Load and process image
    print("Loading local image...")
    image = load_image()

    print("Encoding image...")
    enc_image = model.encode_image(image)

    # Ask questions about the image
    questions = [
        "Describe this image.",
        "What colors are prominent in this image?",
        "Is this an icon or logo? If so, describe its design.",
    ]

    print("\nAsking questions about the image:")
    for question in questions:
        print(f"\nQ: {question}")
        answer = model.answer_question(enc_image, question, tokenizer)
        print(f"A: {answer}")


if __name__ == "__main__":
    main()
