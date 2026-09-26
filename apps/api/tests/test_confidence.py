import pytest
from modules.confidence.service import compute_composite_confidence


def test_confidence_formula():
    # High confidence case
    high_score = compute_composite_confidence(
        faithfulness=0.95,
        top_reranker_score=0.85,
        coverage=1.0,
        latency_ms=1200,
    )
    assert high_score >= 0.75

    # Low confidence case
    low_score = compute_composite_confidence(
        faithfulness=0.30,
        top_reranker_score=0.20,
        coverage=0.2,
        latency_ms=8000,
    )
    assert low_score < 0.50
