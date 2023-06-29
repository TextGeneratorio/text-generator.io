from app import image_caption_np
import cv2

def test_image_caption_np():
    # load image as opencv from data/stepping_stones
    image = cv2.imread("examples/stepping_stones.jpeg")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    caption = image_caption_np(image)
    print(caption)
