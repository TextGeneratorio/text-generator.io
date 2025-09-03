import io

from PIL import Image

from questions.screenshot_utils import process_image


def test_process_image_downscales():
    # create a simple image larger than allowed
    img = Image.new("RGB", (2000, 1500), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = process_image(buf.getvalue())
    processed = Image.open(io.BytesIO(result))
    assert processed.width <= 1092 and processed.height <= 1568
