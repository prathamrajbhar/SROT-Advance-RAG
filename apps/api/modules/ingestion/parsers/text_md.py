"""Plain-text and Markdown parser returning typed ParsedElement objects.

Heading levels are detected from leading ``#`` characters.  The heading
breadcrumb (``heading_path``) is maintained as a stack and attached to
every paragraph element so downstream retrieval has section context.
"""
from __future__ import annotations

import logging
import re
from typing import List

from modules.ingestion.chunker import ParsedElement, _advance_path

logger = logging.getLogger(__name__)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)")


def parse_text_markdown(content_bytes: bytes, filename: str) -> List[ParsedElement]:
    """Parse plain text / Markdown into typed ParsedElement objects.

    Strategy:
    * Lines that match ``# Heading`` patterns → ``heading`` elements.
    * Blank lines flush the current paragraph buffer.
    * Trailing non-empty lines are flushed at EOF.
    * Files with no structure at all → single ``paragraph`` element.
    """
    text = content_bytes.decode("utf-8", errors="replace")
    lines = text.splitlines()
    elements: List[ParsedElement] = []
    heading_path: List[str] = []

    para_lines: List[str] = []
    para_start_line = 1
    line_num = 0

    def _flush_para(end_line: int) -> None:
        nonlocal para_lines, para_start_line
        if not para_lines:
            return
        body = "\n".join(para_lines).strip()
        if body:
            elements.append(ParsedElement(
                kind="paragraph",
                content=body,
                locator={"start_line": para_start_line, "end_line": end_line},
                heading_path=list(heading_path),
            ))
        para_lines = []
        para_start_line = end_line + 1

    for line in lines:
        line_num += 1
        m = _HEADING_RE.match(line.strip())

        if m:
            _flush_para(line_num - 1)
            level = len(m.group(1))
            heading_text = m.group(2).strip()
            heading_path = _advance_path(heading_path, heading_text, level)
            elements.append(ParsedElement(
                kind="heading",
                content=line.strip(),
                locator={"line": line_num},
                heading_path=list(heading_path[:-1]),
                heading_level=level,
            ))
            para_start_line = line_num + 1

        elif not line.strip():
            _flush_para(line_num)

        else:
            if not para_lines:
                para_start_line = line_num
            para_lines.append(line)

    _flush_para(line_num)

    # Bare file with no Markdown structure
    if not elements and text.strip():
        elements.append(ParsedElement(
            kind="paragraph",
            content=text.strip(),
            locator={"start_line": 1, "end_line": line_num},
        ))

    logger.debug(
        "parse_text_markdown: '%s' → %d elements", filename, len(elements)
    )
    return elements
