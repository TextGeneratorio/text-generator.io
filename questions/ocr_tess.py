from PIL import Image

import pytesseract
import re
# from PyPDF2 import PdfReader

from questions.utils import log_time

# If you don't have tesseract executable in your PATH, include the following:
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"
# Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'

def ocr_tess(image) -> str:
    with log_time("OCR"):
        image_text = pytesseract.image_to_string(image)
    cleaned_text = clean_text(image_text)
    return cleaned_text


cleaning_regex = re.compile(r"(\s)\s*")


def clean_text(text: str) -> str:
    """
    remove artefacts from OCR that are not helpful
    """

    return cleaning_regex.sub(r"\1", text).strip()


# def get_pdf_text(pdf_file):
#     reader = PdfReader("example.pdf")
#     text = ""
#     for page in reader.pages:
#         text += page.extract_text() + "\n"


"""

import fitz
doc = fitz.open(filename)
doc.page_count 
page = doc.load_page(pno)
text = page.get_text(opt)
"""

# Simple image to string
# print(ocr_tess(Image.open("/home/lee/Pictures/20200505_145909.jpg")))
""
# # In order to bypass the image conversions of pytesseract, just use relative or absolute image path
# # NOTE: In this case you should provide tesseract supported images or tesseract will return error
# print(pytesseract.image_to_string('test.png'))
#
# # text = pytesseract.image_to_string(cv2.imread('ocr.png'), lang='eng')
# # List of available languages
# print(pytesseract.get_languages(config=''))
#
# # French text image to string
# print(pytesseract.image_to_string(Image.open('test-european.jpg'), lang='fra'))
#
# # Batch processing with a single file containing the list of multiple image file paths
# print(pytesseract.image_to_string('images.txt'))
