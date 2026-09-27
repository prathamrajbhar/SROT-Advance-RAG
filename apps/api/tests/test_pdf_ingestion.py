import io
import pytest
import pypdf
from modules.ingestion.chunker import chunk_elements
from modules.ingestion.parsers.pdf_docx import parse_pdf


@pytest.mark.asyncio
async def test_pdf_parsing_multipage_scanned():
    writer = pypdf.PdfWriter()
    for _ in range(4):
        writer.add_blank_page(width=300, height=300)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    elements = await parse_pdf(pdf_bytes)
    assert len(elements) == 4
    for i, elem in enumerate(elements):
        assert elem["locator"]["page_number"] == i + 1

    chunks = chunk_elements(elements)
    assert len(chunks) == 4
    assert chunks[0]["locator"]["page_number"] == 1
    assert chunks[3]["locator"]["page_number"] == 4
