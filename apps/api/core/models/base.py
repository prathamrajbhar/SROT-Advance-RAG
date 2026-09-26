from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    model: str
    provider: str
    raw: Optional[Dict[str, Any]] = None


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        pass


class BaseEmbedder(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self, query: str, candidates: List[str], top_k: int = 8
    ) -> List[Tuple[int, float]]:
        pass


class BaseWhisper(ABC):
    @abstractmethod
    async def transcribe(
        self, audio_bytes: bytes, filename: str
    ) -> List[Dict[str, Any]]:
        pass
