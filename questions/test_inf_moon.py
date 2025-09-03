import logging
import os

from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer

from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def test_moondream():
    model_id = "vikhyatk/moondream2"
    revision = "2024-08-26"

    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, revision=revision)
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)

    # Test with a sample image
    image_path = "static/img/me.jpg"
    assert os.path.exists(image_path), f"Test image not found at {image_path}"

    image = Image.open(image_path)
    enc_image = model.encode_image(image)

    # Test basic image description
    response = model.answer_question(enc_image, "Describe this image.", tokenizer)
    logger.info(f"Image description: {response}")
    assert isinstance(response, str)
    assert len(response) > 0

    # Test specific question
    question = "What colors are present in this image?"
    response = model.answer_question(enc_image, question, tokenizer)
    logger.info(f"Question: {question}\nAnswer: {response}")
    assert isinstance(response, str)
    assert len(response) > 0


if __name__ == "__main__":
    test_moondream()
