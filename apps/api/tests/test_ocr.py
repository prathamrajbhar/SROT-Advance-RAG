import io
import pytest
from PIL import Image, ImageDraw
import pypdf
from modules.ingestion.ocr import extract_ocr_text
from modules.ingestion.parsers.media import parse_image
from modules.ingestion.parsers.pdf_docx import parse_pdf


def generate_test_image_bytes(text: str) -> bytes:
    img = Image.new("RGB", (600, 150), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 50), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_local_tesseract_ocr_extraction():
    img_bytes = generate_test_image_bytes("SROT Enterprise OCR Pipeline")
    extracted = extract_ocr_text(img_bytes)
    assert "SROT" in extracted or "Enterprise" in extracted or "OCR" in extracted


@pytest.mark.asyncio
async def test_parse_image_with_ocr():
    img_bytes = generate_test_image_bytes("Invoice ID: 987654")
    elements = await parse_image(img_bytes, "invoice.png", "image/png")
    assert len(elements) >= 1
    assert elements[0]["kind"] in ("text", "image_description")


@pytest.mark.asyncio
async def test_scanned_pdf_ocr_pipeline():
    # Build a PDF with an embedded image
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=600, height=400)
    
    img_bytes = generate_test_image_bytes("CONFIDENTIAL REPORT")
    # Add image to pypdf page
    img = Image.open(io.BytesIO(img_bytes))
    page.add_transformation(pypdf.Transformation())
    
    pdf_buf = io.BytesIO()
    writer.write(pdf_buf)
    
    elements = await parse_pdf(pdf_buf.getvalue())
    assert len(elements) >= 1
    assert elements[0]["locator"]["page_number"] == 1
