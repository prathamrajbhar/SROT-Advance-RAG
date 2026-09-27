import io
import zlib
from typing import Any, Dict, List, Tuple
import docx
from pypdf import PdfReader


def extract_page_images(page: Any, page_num: int) -> List[Tuple[bytes, str, str]]:
    """Extract embedded images from a PDF page using pure python XObject stream decompression."""
    images: List[Tuple[bytes, str, str]] = []

    # 1. Try pypdf page.images (if Pillow is installed)
    try:
        for img_idx, img_file in enumerate(page.images):
            img_name = getattr(img_file, "name", f"page_{page_num}_img_{img_idx+1}.png")
            images.append((img_file.data, img_name, "image/png"))
    except Exception:
        pass

    # 2. Pure python XObject stream extraction
    if not images:
        try:
            resources = page.get("/Resources", {})
            if hasattr(resources, "get_object"):
                resources = resources.get_object()
            if isinstance(resources, dict) and "/XObject" in resources:
                xobjects = resources["/XObject"]
                if hasattr(xobjects, "get_object"):
                    xobjects = xobjects.get_object()
                for obj_name, obj in xobjects.items():
                    if hasattr(obj, "get_object"):
                        obj = obj.get_object()
                    if isinstance(obj, dict) and obj.get("/Subtype") == "/Image":
                        raw_data = getattr(obj, "_data", None)
                        if not raw_data and hasattr(obj, "get_data"):
                            raw_data = obj.get_data()
                        if raw_data:
                            filter_type = str(obj.get("/Filter", ""))
                            if "/FlateDecode" in filter_type:
                                try:
                                    raw_data = zlib.decompress(raw_data)
                                except Exception:
                                    pass
                            mime = "image/jpeg" if raw_data.startswith(b"\xff\xd8\xff") else "image/png"
                            ext = "jpg" if mime == "image/jpeg" else "png"
                            clean_name = f"page_{page_num}_{str(obj_name).lstrip('/')}.{ext}"
                            images.append((raw_data, clean_name, mime))
        except Exception:
            pass

    return images


async def parse_pdf(content_bytes: bytes) -> List[Dict[str, Any]]:
    from modules.ingestion.parsers.media import parse_image

    elements: List[Dict[str, Any]] = []
    reader = PdfReader(io.BytesIO(content_bytes))

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text() or ""
        paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]

        if paragraphs:
            for p in paragraphs:
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
        else:
            # Scanned / image-only PDF page
            page_imgs = extract_page_images(page, page_num)
            page_has_content = False
            for img_bytes, img_name, mime in page_imgs:
                try:
                    img_elements = await parse_image(img_bytes, img_name, mime)
                    for elem in img_elements:
                        elem["locator"]["page_number"] = page_num
                        elements.append(elem)
                        page_has_content = True
                except Exception:
                    pass

            if not page_has_content:
                elements.append({
                    "kind": "text",
                    "content": f"Page {page_num} of {len(reader.pages)}: Scanned page visual record.",
                    "locator": {"page_number": page_num},
                })

    if not elements:
        elements.append({
            "kind": "text",
            "content": f"PDF document containing {len(reader.pages)} pages.",
            "locator": {"page_number": 1},
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
