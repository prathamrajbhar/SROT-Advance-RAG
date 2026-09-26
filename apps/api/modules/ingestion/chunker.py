import hashlib
import uuid
from typing import Any, Dict, List, Optional, Tuple
from core.config import get_settings

settings = get_settings()


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_elements(
    elements: List[Dict[str, Any]],
    child_token_limit: int = 250,
    parent_token_limit: int = 1500,
) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    current_parent_id: Optional[uuid.UUID] = None
    current_parent_tokens = 0

    for el in elements:
        content = el["content"].strip()
        if not content:
            continue

        tokens = estimate_tokens(content)

        # Split large content into child chunks if needed
        words = content.split()
        if len(words) > child_token_limit:
            sub_chunks = []
            for i in range(0, len(words), child_token_limit):
                sub_text = " ".join(words[i : i + child_token_limit])
                sub_chunks.append(sub_text)
        else:
            sub_chunks = [content]

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

            chunks.append({
                "id": child_id,
                "parent_id": assigned_parent_id,
                "chunk_index": chunk_index,
                "kind": el.get("kind", "text"),
                "token_count": sub_tokens,
                "content": sub_text,
                "locator": el.get("locator"),
                "content_hash": hash_content(sub_text),
            })
            chunk_index += 1

    return chunks
