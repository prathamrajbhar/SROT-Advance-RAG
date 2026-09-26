import re
from typing import Any, Dict, List, Tuple

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
PAN_REGEX = re.compile(r"[A-Z]{5}[0-9]{4}[A-Z]{1}")
AADHAAR_REGEX = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")


def scan_pii(text: str) -> Tuple[Dict[str, Any], bool]:
    kinds: List[str] = []
    total_matches = 0

    if EMAIL_REGEX.search(text):
        kinds.append("email")
        total_matches += len(EMAIL_REGEX.findall(text))
    if PHONE_REGEX.search(text):
        kinds.append("phone")
        total_matches += len(PHONE_REGEX.findall(text))
    if PAN_REGEX.search(text):
        kinds.append("pan")
        total_matches += len(PAN_REGEX.findall(text))
    if AADHAAR_REGEX.search(text):
        kinds.append("aadhaar")
        total_matches += len(AADHAAR_REGEX.findall(text))
    if CARD_REGEX.search(text):
        kinds.append("credit_card")
        total_matches += len(CARD_REGEX.findall(text))

    has_pii = len(kinds) > 0
    words_count = max(1, len(text.split()))
    density_ratio = total_matches / words_count

    if density_ratio > 0.05:
        density = "high"
    elif density_ratio > 0.01:
        density = "medium"
    elif has_pii:
        density = "low"
    else:
        density = "none"

    flags = {
        "density": density,
        "kinds": kinds,
        "match_count": total_matches,
    }
    return flags, has_pii
