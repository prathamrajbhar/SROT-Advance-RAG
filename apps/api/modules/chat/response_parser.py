import json
import re
from typing import Any, Dict, List, Tuple


def extract_llm_json_response(raw_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts sanitized markdown answer and claims from an LLM response string.
    Handles raw JSON, markdown-fenced JSON, multi-line unescaped control chars,
    partial JSON, and unescaped newlines.
    """
    if not raw_text or not raw_text.strip():
        return "", []

    cleaned = raw_text.strip()

    # 1. Strip markdown code fences if wrapped in ```json ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    # 2. Try direct JSON parsing with strict=False (allows unescaped newlines/tabs)
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

    # 4. Extract answer_md and claims using robust multi-line regex
    answer_match = re.search(r'"answer_md"\s*:\s*"([\s\S]*?)(?="\s*,\s*"claims"|"\s*\}\s*$|\Z)', cleaned)
    if answer_match:
        extracted = answer_match.group(1)
        claims = _extract_claims_fallback(cleaned)
        return _normalize_text(extracted), claims

    # 5. If JSON claims residue exists in text, strip it out
    if '"claims"' in cleaned:
        cleaned = re.sub(r',\s*"claims"\s*:\s*\[[\s\S]*?\]\s*\}?', '', cleaned)
        cleaned = re.sub(r'\{\s*"answer_md"\s*:\s*"?', '', cleaned)
        cleaned = cleaned.rstrip('"} \n')

    return _normalize_text(cleaned), []


def _normalize_text(text: str) -> str:
    """Normalizes escaped newlines, quotes, and whitespace."""
    if not text:
        return ""
    # Replace literal escaped \n and \r with actual newlines
    normalized = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    # Replace escaped quotes
    normalized = normalized.replace('\\"', '"')
    return normalized.strip()


def _extract_claims_fallback(raw_text: str) -> List[Dict[str, Any]]:
    """Attempts to parse the claims array if JSON parsing failed."""
    claims_match = re.search(r'"claims"\s*:\s*(\[[\s\S]*?\])', raw_text)
    if not claims_match:
        return []
    try:
        parsed = json.loads(claims_match.group(1), strict=False)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []
