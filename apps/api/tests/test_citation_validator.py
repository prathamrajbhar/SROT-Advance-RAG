import pytest
from modules.chat.citation_validator import validate_citations_sync


def test_validate_citations_success():
    retrieved = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "document_name": "report.pdf",
            "content": "Net-30 payment terms are strictly enforced.",
            "locator": {"page_number": 3},
        }
    ]
    claims = [
        {"text": "Payment terms are Net-30.", "citation_ids": ["c1"]}
    ]

    all_valid, citations, coverage = validate_citations_sync(claims, retrieved)
    assert all_valid
    assert len(citations) == 1
    assert coverage == 1.0
    assert citations[0]["document_name"] == "report.pdf"


def test_validate_citations_invalid_id():
    retrieved = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "document_name": "report.pdf",
            "content": "Content here",
        }
    ]
    claims = [
        {"text": "Fake claim", "citation_ids": ["fake_nonexistent_id"]}
    ]

    all_valid, citations, coverage = validate_citations_sync(claims, retrieved)
    assert not all_valid
    assert len(citations) == 0
    assert coverage == 0.0
