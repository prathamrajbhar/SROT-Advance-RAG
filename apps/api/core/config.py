import json
from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database & Cache
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/srot"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    # Storage (AWS S3 or LocalStack)
    S3_ENDPOINT_URL: Optional[str] = "http://localhost:4566"
    S3_REGION: str = "us-east-1"
    S3_BUCKET: str = "srot"
    S3_ACCESS_KEY: str = "test"
    S3_SECRET_KEY: str = "test"

    # AWS Environment Variables
    AWS_ENDPOINT_URL: Optional[str] = None
    AWS_DEFAULT_REGION: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "change_this_to_a_secure_random_string_min_32_chars"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM Provider
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama3.1:8b"
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = "http://localhost:11434/v1"

    # Embeddings, Reranker & Whisper
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDER_URL: str = "http://localhost:8001"
    RERANKER_PROVIDER: str = "local"
    RERANKER_URL: str = "http://localhost:8002"
    WHISPER_URL: str = "http://localhost:8003"
    INTERNAL_MODEL_TOKEN: str = "internal_secret_token"

    # Tracing
    LANGFUSE_HOST: Optional[str] = "http://localhost:3001"
    LANGFUSE_PUBLIC_KEY: Optional[str] = "pk-lf-test"
    LANGFUSE_SECRET_KEY: Optional[str] = "sk-lf-test"

    # Tuning
    RERANK_MIN_SCORE: float = 0.35
    CHUNK_CHILD_TOKENS: int = 250
    CHUNK_PARENT_TOKENS: int = 1500
    HYBRID_TOP_K: int = 40
    LLM_TOP_K_PARENTS: int = 8
    RATE_LIMIT_CHAT_PER_HOUR: int = 60

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: object) -> str:
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
            return v
        return str(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        if isinstance(v, list):
            return [str(item) for item in v]
        return ["http://localhost:3000"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
