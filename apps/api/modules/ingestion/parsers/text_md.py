from typing import Any, Dict, List


def parse_text_markdown(content_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    text = content_bytes.decode("utf-8", errors="replace")
    lines = text.splitlines()
    elements: List[Dict[str, Any]] = []

    current_section = []
    current_heading = None
    line_number = 1

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_section:
                section_text = "\n".join(current_section).strip()
                if section_text:
                    elements.append({
                        "kind": "text",
                        "content": section_text,
                        "locator": {"heading": current_heading, "start_line": line_number - len(current_section)},
                    })
                current_section = []
            current_heading = stripped.lstrip("#").strip()
            elements.append({
                "kind": "heading",
                "content": stripped,
                "locator": {"line": line_number},
            })
        elif stripped:
            current_section.append(line)
        line_number += 1

    if current_section:
        section_text = "\n".join(current_section).strip()
        if section_text:
            elements.append({
                "kind": "text",
                "content": section_text,
                "locator": {"heading": current_heading, "start_line": line_number - len(current_section)},
            })

    if not elements and text.strip():
        elements.append({
            "kind": "text",
            "content": text.strip(),
            "locator": {"line": 1},
        })

    return elements
