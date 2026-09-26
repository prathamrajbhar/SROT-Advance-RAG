import io
from typing import Any, Dict, List
import docx
from pypdf import PdfReader


def parse_pdf(content_bytes: bytes) -> List[Dict[str, Any]]:
    elements: List[Dict[str, Any]] = []
    reader = PdfReader(io.BytesIO(content_bytes))

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text() or ""
        paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]

        for p in paragraphs:
            # Check if likely a heading
            if len(p) < 80 and not p.endswith("."):
                elements.append({
                    "kind": "heading",
                    "content": p,
                    "locator": {"page_number": page_num},
                })
            else:
                elements.append({
                    "kind": "text",
                    "content": p,
                    "locator": {"page_number": page_num},
                })
    return elements


def parse_docx(content_bytes: bytes) -> List[Dict[str, Any]]:
    elements: List[Dict[str, Any]] = []
    doc = docx.Document(io.BytesIO(content_bytes))

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        if p.style and p.style.name and p.style.name.startswith("Heading"):
            elements.append({
                "kind": "heading",
                "content": text,
                "locator": {"style": p.style.name},
            })
        else:
            elements.append({
                "kind": "text",
                "content": text,
                "locator": {"style": "Normal"},
            })

    for table in doc.tables:
        table_rows = []
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells]
            table_rows.append(" | ".join(row_cells))
        if table_rows:
            elements.append({
                "kind": "table_row",
                "content": "\n".join(table_rows),
                "locator": {"rows": len(table_rows)},
            })

    return elements
