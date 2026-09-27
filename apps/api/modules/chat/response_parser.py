import json
import re
from typing import Any, Dict, List, Tuple


def extract_llm_json_response(raw_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts sanitized markdown answer and claims from an LLM response string.
    Handles raw JSON, markdown-fenced JSON, multi-line unescaped control chars,
    pseudo-structured markdown with 'Answer'/'Claims' headers, and raw text.
    """
    if not raw_text or not raw_text.strip():
        return "", []

    cleaned = raw_text.strip()

    # 1. Strip markdown code fences if entire text is wrapped in ```json ... ```
    if cleaned.startswith("```json") or (cleaned.startswith("```") and "Answer in Markdown" not in cleaned and "{" in cleaned):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    # 2. Try direct JSON parsing
    try:
        parsed = json.loads(cleaned, strict=False)
        if isinstance(parsed, dict):
            answer_md = parsed.get("answer_md", "")
            claims = parsed.get("claims", [])
            if isinstance(answer_md, str) and answer_md.strip():
                return _normalize_text(answer_md), claims if isinstance(claims, list) else []
    except Exception:
        pass

    # 3. Try finding the outermost JSON object
    json_match = re.search(r"(\{[\s\S]*\})", cleaned)
    if json_match:
        candidate_json = json_match.group(1)
        try:
            parsed = json.loads(candidate_json, strict=False)
            if isinstance(parsed, dict):
                answer_md = parsed.get("answer_md", "")
                claims = parsed.get("claims", [])
                if isinstance(answer_md, str) and answer_md.strip():
                    return _normalize_text(answer_md), claims if isinstance(claims, list) else []
        except Exception:
            pass

    # 4. Extract from "Answer in Markdown" block if LLM printed schema headers
    md_answer_match = re.search(r"(?:Answer in Markdown|Markdown Answer)\s*:?\s*\n*```(?:markdown)?\s*([\s\S]*?)\s*```", cleaned, flags=re.IGNORECASE)
    if md_answer_match:
        extracted_answer = md_answer_match.group(1).strip()
        claims = _extract_claims_from_prose(cleaned)
        return _normalize_text(extracted_answer), claims

    # 5. Extract answer_md and claims using regex from partial JSON
    answer_match = re.search(r'"answer_md"\s*:\s*"([\s\S]*?)(?="\s*,\s*"claims"|"\s*\}\s*$|\Z)', cleaned)
    if answer_match:
        extracted = answer_match.group(1)
        claims = _extract_claims_from_prose(cleaned)
        return _normalize_text(extracted), claims

    # 6. Clean pseudo-structured prose (strip "Answer", "Claims", "Answer in Markdown")
    claims = _extract_claims_from_prose(cleaned)
    cleaned = re.sub(r"(?:^|\n)#*\s*Claims\s*\n+[\s\S]*?(?=(?:^|\n)#*\s*Answer|\Z)", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?:^|\n)#*\s*Answer in Markdown\s*\n+[\s\S]*?(?=\Z)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^(?:#*\s*Answer\s*:?\s*\n+)", "", cleaned.strip(), flags=re.IGNORECASE)

    # If JSON claims residue exists in text, strip it out
    if '"claims"' in cleaned:
        cleaned = re.sub(r',\s*"claims"\s*:\s*\[[\s\S]*?\]\s*\}?', '', cleaned)
        cleaned = re.sub(r'\{\s*"answer_md"\s*:\s*"?', '', cleaned)
        cleaned = cleaned.rstrip('"} \n')

    return _normalize_text(cleaned), claims


def _normalize_text(text: str) -> str:
    """Normalizes escaped newlines, quotes, and whitespace."""
    if not text:
        return ""
    normalized = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    normalized = normalized.replace('\\"', '"')
    return normalized.strip()


def _extract_claims_from_prose(raw_text: str) -> List[Dict[str, Any]]:
    """Extracts claim statements and UUID citation IDs from unstructured prose/tables."""
    claims = []
    uuid_pattern = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    for line in raw_text.split("\n"):
        if "|" in line:
            uuids = re.findall(uuid_pattern, line, re.IGNORECASE)
            if uuids:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                claim_text = parts[0] if parts else "Factual statement"
                claims.append({"text": claim_text, "citation_ids": uuids})

    if not claims:
        claims_match = re.search(r'"claims"\s*:\s*(\[[\s\S]*?\])', raw_text)
        if claims_match:
            try:
                parsed = json.loads(claims_match.group(1), strict=False)
                if isinstance(parsed, list):
                    claims = parsed
            except Exception:
                pass
    return claims
