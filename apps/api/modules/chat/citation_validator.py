from typing import Any, Dict, List, Set, Tuple
from core.models.factory import get_llm_client


def validate_citations_sync(
    claims: List[Dict[str, Any]],
    retrieved_contexts: List[Dict[str, Any]],
) -> Tuple[bool, List[Dict[str, Any]], float]:
    valid_ids: Set[str] = {c["chunk_id"] for c in retrieved_contexts}
    context_map = {c["chunk_id"]: c for c in retrieved_contexts}

    valid_citations: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    total_claims = max(1, len(claims))
    supported_claims = 0
    all_valid = True

    index = 1
    for claim in claims:
        claim_cids = claim.get("citation_ids", [])
        has_support = False
        for cid in claim_cids:
            cid_str = str(cid)
            if cid_str in valid_ids:
                has_support = True
                if cid_str not in seen_ids:
                    seen_ids.add(cid_str)
                    ctx = context_map[cid_str]
                    valid_citations.append({
                        "index": index,
                        "chunk_id": ctx["chunk_id"],
                        "document_id": ctx["document_id"],
                        "document_name": ctx["document_name"],
                        "locator": ctx.get("locator"),
                        "snippet": ctx["content"][:200] + ("..." if len(ctx["content"]) > 200 else ""),
                    })
                    index += 1
            else:
                all_valid = False

        if has_support:
            supported_claims += 1

    coverage = supported_claims / total_claims
    return all_valid, valid_citations, coverage
