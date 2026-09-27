"""PDF and DOCX parsers — produce typed ParsedElement objects.

PDF:   text is extracted per page; short non-punctuated lines become headings.
       Scanned/image-only pages are OCR-processed via the image parser.
DOCX:  paragraphs and tables are iterated in document body order so table
       position relative to prose is preserved. Word heading styles give
       exact heading levels.

Image extraction from PDFs is best-effort: if the PDF library cannot decode a
specific image, that image is skipped with a logged warning — the rest of the
document continues to parse normally.
"""
from __future__ import annotations

import io
import logging
import re
import zlib
from typing import Any, Generator, Tuple

import docx
import docx.table
import docx.text.paragraph
from docx.oxml.ns import qn
from pypdf import PdfReader

from modules.ingestion.chunker import ParsedElement, _advance_path
from modules.ingestion.parsers.media import parse_image

logger = logging.getLogger(__name__)

# PDF heading heuristic: short lines (≤ 15 words, ≤ 100 chars) that do not
# end with punctuation are treated as headings. All such headings are level 1
# because PDF has no semantic style information.
_PDF_HEADING_MAX_WORDS = 15
_PDF_HEADING_MAX_CHARS = 100


# ─── PDF helpers ──────────────────────────────────────────────────────────────


def _is_pdf_heading(text: str) -> bool:
    words = text.split()
    return (
        bool(words)
        and re.search(r"[A-Za-z]", text) is not None
        and 1 <= len(words) <= _PDF_HEADING_MAX_WORDS
        and len(text) <= _PDF_HEADING_MAX_CHARS
        and text[-1] not in ".?!,"
    )


def _extract_page_images(page: Any, page_num: int) -> list[Tuple[bytes, str, str]]:
    """Return (raw_bytes, name, mime_type) for every image on a PDF page.

    Attempts two strategies:
    1. pypdf's high-level page.images API (requires Pillow).
    2. Direct XObject stream extraction with FlateDecode decompression.

    Failures from either strategy are logged at DEBUG level and do not
    abort parsing — the caller decides whether to continue without images.
    """
    images: list[Tuple[bytes, str, str]] = []

    # Strategy 1: pypdf page.images
    try:
        for idx, img in enumerate(page.images):
            name = getattr(img, "name", f"page_{page_num}_img_{idx}.png")
            images.append((img.data, name, "image/png"))
    except Exception as exc:
        logger.debug("PDF page %d: pypdf.page.images failed: %s", page_num, exc)

    if images:
        return images

    # Strategy 2: Raw XObject stream extraction
    try:
        resources = page.get("/Resources", {})
        if hasattr(resources, "get_object"):
            resources = resources.get_object()
        xobj_map = (resources or {}).get("/XObject", {})
        if hasattr(xobj_map, "get_object"):
            xobj_map = xobj_map.get_object()

        for obj_name, obj_ref in (xobj_map or {}).items():
            obj = obj_ref.get_object() if hasattr(obj_ref, "get_object") else obj_ref
            if not (isinstance(obj, dict) and obj.get("/Subtype") == "/Image"):
                continue

            raw: bytes | None = getattr(obj, "_data", None)
            if raw is None and hasattr(obj, "get_data"):
                raw = obj.get_data()
            if not raw:
                continue

            if "/FlateDecode" in str(obj.get("/Filter", "")):
                try:
                    raw = zlib.decompress(raw)
                except zlib.error as decomp_exc:
                    logger.debug(
                        "PDF page %d: FlateDecode decompression failed for %s: %s",
                        page_num, obj_name, decomp_exc,
                    )
                    continue

            mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "image/png"
            ext = "jpg" if mime == "image/jpeg" else "png"
            images.append((raw, f"page_{page_num}_{str(obj_name).lstrip('/')}.{ext}", mime))

    except Exception as exc:
        logger.debug("PDF page %d: XObject extraction failed: %s", page_num, exc)

    return images


# ─── PDF parser ───────────────────────────────────────────────────────────────


async def parse_pdf(content_bytes: bytes) -> list[ParsedElement]:
    """Parse a PDF into typed ParsedElement objects.

    Text pages → paragraph/heading elements.
    Scanned pages → OCR via parse_image; if OCR yields nothing, a descriptive
    placeholder is emitted so the chunk is not silently lost.
    """
    elements: list[ParsedElement] = []
    reader = PdfReader(io.BytesIO(content_bytes))
    heading_path: list[str] = []

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text() or ""
        blocks = [b.strip() for b in page_text.split("\n\n") if b.strip()]

        if not blocks:
            # Scanned page — attempt OCR on embedded images.
            page_images = _extract_page_images(page, page_num)
            got_content = False

            for img_bytes, img_name, mime in page_images:
                try:
                    img_elements = await parse_image(img_bytes, img_name, mime)
                except Exception as exc:
                    logger.warning(
                        "PDF page %d: OCR failed for image %s: %s",
                        page_num, img_name, exc,
                    )
                    continue

                for el in img_elements:
                    el.locator["page_number"] = page_num
                    elements.append(el)
                    got_content = True

            if not got_content:
                elements.append(ParsedElement(
                    kind="paragraph",
                    content=f"[Page {page_num} of {len(reader.pages)}: scanned, no extractable text]",
                    locator={"page_number": page_num},
                    heading_path=list(heading_path),
                ))
            continue

        for block in blocks:
            if _is_pdf_heading(block):
                heading_path = _advance_path(heading_path, block, 1)
                elements.append(ParsedElement(
                    kind="heading",
                    content=block,
                    locator={"page_number": page_num},
                    heading_path=list(heading_path[:-1]),
                    heading_level=1,
                ))
            else:
                elements.append(ParsedElement(
                    kind="paragraph",
                    content=block,
                    locator={"page_number": page_num},
                    heading_path=list(heading_path),
                ))

    return elements


# ─── DOCX helpers ────────────────────────────────────────────────────────────


def _iter_docx_body(doc: Any) -> Generator[Tuple[str, Any], None, None]:
    """Yield ('paragraph', Paragraph) or ('table', Table) in document order."""
    for child in doc.element.body:
        if child.tag == qn("w:p"):
            yield "paragraph", docx.text.paragraph.Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield "table", docx.table.Table(child, doc)


# ─── DOCX parser ─────────────────────────────────────────────────────────────


def parse_docx(content_bytes: bytes) -> list[ParsedElement]:
    """Parse a DOCX into typed ParsedElement objects.

    Iterates the document XML body so paragraphs and tables appear in their
    original order. Word heading styles (Heading 1…6) give exact levels.
    Tables are emitted as single atomic ``table`` elements.
    """
    elements: list[ParsedElement] = []
    doc = docx.Document(io.BytesIO(content_bytes))
    heading_path: list[str] = []
    para_index = 0

    for block_kind, block in _iter_docx_body(doc):
        if block_kind == "paragraph":
            text = block.text.strip()
            if not text:
                continue

            style_name: str = (block.style.name or "") if block.style else ""

            if style_name.startswith("Heading"):
                try:
                    level = int(style_name.split()[-1])
                except (ValueError, IndexError):
                    level = 1
                heading_path = _advance_path(heading_path, text, level)
                elements.append(ParsedElement(
                    kind="heading",
                    content=text,
                    locator={"style": style_name, "para_index": para_index},
                    heading_path=list(heading_path[:-1]),
                    heading_level=level,
                ))
            else:
                elements.append(ParsedElement(
                    kind="paragraph",
                    content=text,
                    locator={"style": style_name or "Normal", "para_index": para_index},
                    heading_path=list(heading_path),
                ))
            para_index += 1

        elif block_kind == "table":
            rows = [
                " | ".join(cell.text.strip() for cell in row.cells)
                for row in block.rows
            ]
            if rows:
                elements.append(ParsedElement(
                    kind="table",
                    content="\n".join(rows),
                    locator={"rows": len(rows)},
                    heading_path=list(heading_path),
                ))

    return elements
