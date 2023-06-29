from PIL import Image


def scale_down(image: Image, max_width_or_height=312):
    """
    Scales down an image to a given max height or width (small for fast processing)
    """
    width, height = image.size
    if width < max_width_or_height and height < max_width_or_height:
        return image

    if width > height:
        # landscape
        ratio = max_width_or_height / width
        new_height = int(height * ratio)
        new_width = max_width_or_height
    else:
        # portrait
        ratio = max_width_or_height / height
        new_width = int(width * ratio)
        new_height = max_width_or_height
    return image.resize((new_width, new_height), Image.BICUBIC)
