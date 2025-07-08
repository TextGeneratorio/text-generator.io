import os
import importlib.util
import pytest
from PIL import Image
from transformers import pipeline
from questions.logging_config import setup_logging

# Skip the tests if torch is not available as the transformers pipelines
# require it for model execution.
if importlib.util.find_spec("torch") is None:
    pytest.skip("torch is required for Gemma tests", allow_module_level=True)

setup_logging()

def test_gemma_image_captioning():
    model_id = "yujiepan/gemma-3n-tiny-random"
    pipe = pipeline(
        "image-text-to-text",
        model=model_id,
        device=-1,
    )

    image_path = "static/img/me.jpg"
    assert os.path.exists(image_path)
    img = Image.open(image_path)

    messages = [
        {"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": "Describe this image."}]},
    ]
    output = pipe(text=messages, max_new_tokens=5)
    assert isinstance(output[0]["generated_text"][-1]["content"], str)


def test_gemma_text_generation():
    model_id = "yujiepan/gemma-3n-tiny-random"
    text_pipe = pipeline("text-generation", model=model_id, device=-1)
    out = text_pipe("Hello", max_new_tokens=5)
    assert isinstance(out[0]["generated_text"], str)

