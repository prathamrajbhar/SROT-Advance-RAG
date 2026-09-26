import pytest
from modules.chat.response_parser import extract_llm_json_response


def test_clean_json_response():
    raw = '{"answer_md": "## Title\\nThis is a response.", "claims": [{"text": "claim 1", "citation_ids": ["id-1"]}]}'
    answer_md, claims = extract_llm_json_response(raw)
    assert answer_md == "## Title\nThis is a response."
    assert len(claims) == 1
    assert claims[0]["text"] == "claim 1"


def test_markdown_wrapped_json_response():
    raw = """```json
{
  "answer_md": "### Section\\n* Item 1\\n* Item 2",
  "claims": []
}
```"""
    answer_md, claims = extract_llm_json_response(raw)
    assert answer_md == "### Section\n* Item 1\n* Item 2"
    assert claims == []


def test_json_with_surrounding_prose():
    raw = """Here is the result:
{"answer_md": "Direct response content.", "claims": []}
Hope this helps!"""
    answer_md, claims = extract_llm_json_response(raw)
    assert answer_md == "Direct response content."


def test_regex_fallback_on_broken_json():
    raw = '{"answer_md": "Direct markdown text with some quotes: \\"example\\"", "claims": ['  # truncated
    answer_md, claims = extract_llm_json_response(raw)
    assert 'Direct markdown text with some quotes: "example"' in answer_md


def test_raw_markdown_passthrough():
    raw = "Just a raw markdown text without any JSON."
    answer_md, claims = extract_llm_json_response(raw)
    assert answer_md == "Just a raw markdown text without any JSON."
    assert claims == []
