import pytest
from modules.ingestion.chunker import chunk_elements, estimate_tokens, hash_content
from modules.ingestion.pii import scan_pii


def test_estimate_tokens():
    text = "Hello world this is a test"
    assert estimate_tokens(text) == 6


def test_hash_content():
    h1 = hash_content("Test text")
    h2 = hash_content("Test text")
    h3 = hash_content("Different text")
    assert h1 == h2
    assert h1 != h3


def test_chunk_elements():
    elements = [
        {"kind": "heading", "content": "Section 1", "locator": {"line": 1}},
        {"kind": "text", "content": "This is a paragraph under section 1.", "locator": {"line": 2}},
    ]
    chunks = chunk_elements(elements, child_token_limit=10, parent_token_limit=50)
    assert len(chunks) == 2
    assert chunks[0]["kind"] == "heading"
    assert chunks[1]["kind"] == "text"
    assert chunks[0]["parent_id"] is None
    assert chunks[1]["parent_id"] == chunks[0]["id"]


def test_pii_scanner():
    clean_text = "This is a regular business document about marketing strategies."
    flags, has_pii = scan_pii(clean_text)
    assert not has_pii
    assert flags["density"] == "none"

    sensitive_text = "Contact support at user@example.com or call 555-123-4567."
    flags, has_pii = scan_pii(sensitive_text)
    assert has_pii
    assert "email" in flags["kinds"]
    assert "phone" in flags["kinds"]
