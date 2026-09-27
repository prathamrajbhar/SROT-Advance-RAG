import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional
from core.config import get_settings

settings = get_settings()


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def recursive_split_text(
    text: str,
    chunk_size: int = 250,
    chunk_overlap: int = 35,
) -> List[str]:
    """Split text recursively along sentence boundaries with sliding window token overlap."""
    clean_text = text.strip()
    if not clean_text:
        return []

    words = clean_text.split()
    if len(words) <= chunk_size:
        return [clean_text]

    # Sentence boundary regex (split on period, question mark, or exclamation followed by whitespace)
    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", clean_text) if s.strip()]
    if len(sentences) > 1 and all(len(s.split()) <= chunk_size for s in sentences):
        chunks: List[str] = []
        current_words: List[str] = []

        for sentence in sentences:
            s_words = sentence.split()
            if len(current_words) + len(s_words) <= chunk_size:
                current_words.extend(s_words)
            else:
                if current_words:
                    chunks.append(" ".join(current_words))
                    overlap = current_words[-chunk_overlap:] if len(current_words) > chunk_overlap else current_words
                    current_words = overlap + s_words
                else:
                    chunks.append(sentence)

        if current_words:
            chunks.append(" ".join(current_words))
        return chunks

    # Fallback to word-level sliding window
    chunks = []
    step = max(1, chunk_size - chunk_overlap)
    for i in range(0, len(words), step):
        chunk_slice = words[i : i + chunk_size]
        chunks.append(" ".join(chunk_slice))
        if i + chunk_size >= len(words):
            break
    return chunks


def chunk_elements(
    elements: List[Dict[str, Any]],
    child_token_limit: int = 250,
    child_token_overlap: int = 35,
    parent_token_limit: int = 1500,
) -> List[Dict[str, Any]]:
    """Generate enterprise-grade hierarchical parent-child chunks with sentence boundary preservation."""
    chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    current_parent_id: Optional[uuid.UUID] = None
    current_parent_tokens = 0
    active_heading: Optional[str] = None

    for el in elements:
        content = el["content"].strip()
        if not content:
            continue

        kind = el.get("kind", "text")
        if kind == "heading":
            active_heading = content

        # Atomic kinds (headings, table rows) are preserved intact if within bounds
        if kind in ("heading", "table_row") and estimate_tokens(content) <= child_token_limit * 2:
            sub_chunks = [content]
        else:
            sub_chunks = recursive_split_text(
                content,
                chunk_size=child_token_limit,
                chunk_overlap=child_token_overlap,
            )

        for sub_text in sub_chunks:
            sub_tokens = estimate_tokens(sub_text)
            child_id = uuid.uuid4()

            if current_parent_id is None or current_parent_tokens + sub_tokens > parent_token_limit:
                current_parent_id = child_id
                current_parent_tokens = sub_tokens
                assigned_parent_id = None
            else:
                assigned_parent_id = current_parent_id
                current_parent_tokens += sub_tokens

            locator = dict(el.get("locator") or {})
            if active_heading and "heading" not in locator and kind != "heading":
                locator["section_heading"] = active_heading

            chunks.append({
                "id": child_id,
                "parent_id": assigned_parent_id,
                "chunk_index": chunk_index,
                "kind": kind,
                "token_count": sub_tokens,
                "content": sub_text,
                "locator": locator if locator else None,
                "content_hash": hash_content(sub_text),
            })
            chunk_index += 1

    return chunks
