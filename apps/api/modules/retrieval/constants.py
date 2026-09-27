"""Retrieval constants — single source of truth is ``core/config.py``.

All values are read from ``Settings`` at import time so any change in
``.env`` / environment is picked up without touching this file.
No literals are defined here.
"""
from core.config import get_settings as _get_settings

_s = _get_settings()

# Fusion
RRF_K_CONSTANT: int = _s.RRF_K
DEFAULT_HYBRID_TOP_K: int = _s.HYBRID_TOP_K

# Reranking
DEFAULT_RERANK_TOP_K: int = _s.RERANK_TOP_K
RERANK_MIN_SCORE: float = _s.RERANK_MIN_SCORE
RERANK_BATCH_SIZE: int = _s.RERANK_BATCH_SIZE
RERANK_TIMEOUT_S: int = _s.RERANK_TIMEOUT_S

# Context assembly
MAX_PARENT_FETCH_COUNT: int = _s.RERANK_TOP_K
CONTEXT_TOKEN_BUDGET: int = _s.CONTEXT_TOKEN_BUDGET

# Query rewriting
MAX_CONVERSATION_HISTORY_TURNS: int = _s.QUERY_REWRITE_LAST_N_TURNS
