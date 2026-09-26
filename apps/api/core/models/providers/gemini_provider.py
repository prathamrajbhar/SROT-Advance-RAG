import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
from core.models.base import BaseLLMClient, LLMResponse


class GeminiProvider(BaseLLMClient):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            max_retries = 4
            last_error: Optional[Exception] = None
            data = None
            for attempt in range(max_retries):
                try:
                    res = await client.post(url, json=body)
                    if res.status_code in (429, 503) and attempt < max_retries - 1:
                        await asyncio.sleep(2.0 ** attempt)
                        continue
                    if not res.is_success:
                        error_detail = res.text
                        try:
                            err_json = res.json()
                            error_detail = err_json.get("error", {}).get("message", res.text)
                        except Exception:
                            pass
                        raise RuntimeError(f"Gemini API error ({res.status_code}): {error_detail}")
                    data = res.json()
                    break
                except (httpx.ConnectError, httpx.ReadTimeout) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2.0 ** attempt)
                        continue
                    raise RuntimeError(f"Gemini API network error: {str(e)}") from e
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2.0 ** attempt)
                        continue
                    raise e

        if not data:
            if last_error:
                raise last_error
            raise RuntimeError("Failed to receive response from Gemini API")

        candidates = data.get("candidates", [])
        content = ""
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            content = "".join(text_parts)

        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)
        # Cost estimate: ~$0.10 / 1M prompt, $0.40 / 1M completion for flash
        cost_usd = (prompt_tokens * 0.0000001) + (completion_tokens * 0.0000004)

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            model=self.model,
            provider="gemini",
            raw=data,
        )

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        # For simplicity and robust parsing, call generate and stream tokens
        response = await self.generate(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=False,
        )
        words = response.content.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
