import io
from typing import Optional
from PIL import Image
import pytesseract


def extract_ocr_text(image_bytes: bytes, lang: str = "eng") -> str:
    """Extract textual content from image bytes using local Tesseract OCR engine."""
    if not image_bytes:
        return ""

    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Ensure image is in RGB or Grayscale mode
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except Exception as e:
        return ""
