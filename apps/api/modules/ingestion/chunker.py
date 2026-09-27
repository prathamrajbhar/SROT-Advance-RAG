"""Structure-aware parent-child chunker.

Parsers produce ``ParsedElement`` objects. This module groups them into child
chunks (≤ CHUNK_CHILD_TOKENS tokens each) assigned to parent buckets
(≤ CHUNK_PARENT_TOKENS tokens). Every non-heading child is prefixed with the
heading breadcrumb so each chunk is retrieval-complete with no text overlap.

Atomic kinds (table, transcript_segment, sheet_row) are emitted whole — never
split. Headings are never prefixed; they ARE the context anchor.
"""
from __future__ import annotations

import hashlib
import logging
import re
import uuid
from typing import Literal, Optional

from pydantic import BaseModel

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Element kinds ────────────────────────────────────────────────────────────

ElementKind = Literal[
    "heading",
    "paragraph",
    "text",              # accepted from legacy parsers
    "table",
    "list",
    "transcript_segment",
    "sheet_row",
    "image_description",
]

ATOMIC_KINDS: frozenset[str] = frozenset(
    {"table", "transcript_segment", "sheet_row"}
)


# ─── Typed element model ──────────────────────────────────────────────────────


class ParsedElement(BaseModel):
    """One unit of structured content produced by a parser."""

    kind: ElementKind
    content: str
    locator: dict = {}
    heading_path: list[str] = []  # breadcrumb at time of emit
    heading_level: int = 1        # 1-based; only meaningful for "heading"


# ─── Pure helpers ─────────────────────────────────────────────────────────────


def estimate_tokens(text: str) -> int:
    """Word-count token estimate. No external dependencies required."""
    return max(1, len(text.split()))


def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _heading_prefix(path: list[str]) -> str:
    """'Section: A > B — '  or  '' when the document has no headings yet."""
    return ("Section: " + " > ".join(path) + " — ") if path else ""


def _advance_path(path: list[str], text: str, level: int) -> list[str]:
    """Insert heading text at 1-based level, trimming any deeper ancestors."""
    return path[: level - 1] + [text]


def _sentence_children(
    text: str,
    prefix: str,
    limit: int,
) -> list[tuple[str, int]]:
    """Split text at sentence boundaries; return (stored_content, raw_tokens).

    ``raw_tokens`` counts only the original content words — not the prefix —
    so parent-bucket tracking is not distorted by heading-context overhead.
    A sentence longer than ``limit`` is emitted intact: we never break a
    sentence to satisfy the limit.
    """
    sentences = [s for s in re.split(r"(?<=[.?!])\s+", text.strip()) if s.strip()]
    if not sentences:
        raw = estimate_tokens(text)
        return [(prefix + text.strip(), raw)]

    children: list[tuple[str, int]] = []
    batch: list[str] = []
    batch_tokens = 0

    for sentence in sentences:
        s_tokens = estimate_tokens(sentence)
        if batch and batch_tokens + s_tokens > limit:
            children.append((prefix + " ".join(batch), batch_tokens))
            batch, batch_tokens = [], 0
        batch.append(sentence)
        batch_tokens += s_tokens

    if batch:
        children.append((prefix + " ".join(batch), batch_tokens))

    return children


# ─── Public API ───────────────────────────────────────────────────────────────


def chunk_elements(
    elements: list[ParsedElement],
    child_token_limit: Optional[int] = None,
    parent_token_limit: Optional[int] = None,
) -> list[dict]:
    """Convert structured elements into parent-child chunk dicts.

    Parent assignment:
      - The first chunk in each bucket has parent_id = None.
        It acts as the anchor for all subsequent chunks in the bucket.
      - A new bucket starts when adding the next chunk would exceed
        parent_token_limit.

    Returns list[dict] with keys matching the Chunk ORM:
      id, parent_id, chunk_index, kind, token_count, content,
      locator, content_hash.
    """
    child_limit = child_token_limit or settings.CHUNK_CHILD_TOKENS
    parent_limit = parent_token_limit or settings.CHUNK_PARENT_TOKENS

    output: list[dict] = []
    chunk_index = 0
    bucket_id: Optional[uuid.UUID] = None
    bucket_tokens = 0
    heading_path: list[str] = []

    for elem in elements:
        content = elem.content.strip()
        if not content:
            continue

        if elem.kind == "heading":
            clean = content.lstrip("#").strip()
            heading_path = _advance_path(heading_path, clean, elem.heading_level)
            items: list[tuple[str, int]] = [(content, estimate_tokens(content))]

        elif elem.kind in ATOMIC_KINDS:
            active_path = elem.heading_path if elem.heading_path else heading_path
            prefix = _heading_prefix(active_path)
            items = [(prefix + content, estimate_tokens(content))]

        else:
            active_path = elem.heading_path if elem.heading_path else heading_path
            prefix = _heading_prefix(active_path)
            items = _sentence_children(content, prefix, child_limit)

        for stored, raw_tokens in items:
            cid = uuid.uuid4()

            if bucket_id is None or bucket_tokens + raw_tokens > parent_limit:
                bucket_id = cid
                bucket_tokens = raw_tokens
                parent_id: Optional[uuid.UUID] = None
            else:
                parent_id = bucket_id
                bucket_tokens += raw_tokens

            output.append({
                "id": cid,
                "parent_id": parent_id,
                "chunk_index": chunk_index,
                "kind": elem.kind,
                "token_count": raw_tokens,
                "content": stored,
                "locator": dict(elem.locator) if elem.locator else None,
                "content_hash": hash_content(stored),
            })
            chunk_index += 1

    logger.debug("chunk_elements: %d elements → %d chunks", len(elements), len(output))
    return output
