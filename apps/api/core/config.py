import json
from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator, model_validator
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
    LLM_BASE_URL: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    TOGETHER_API_KEY: Optional[str] = None

    # Embeddings, Reranker & Whisper
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    EMBEDDER_URL: str = "http://localhost:11434"
    RERANKER_PROVIDER: str = "local"
    RERANKER_MODEL: str = "BAAI/bge-reranker-large"
    RERANKER_URL: str = "http://localhost:8002"
    WHISPER_URL: str = "http://localhost:8003"
    INTERNAL_MODEL_TOKEN: str = "internal_secret_token"
    MODELS_DIR: Optional[str] = None


    # Tracing
    LANGFUSE_HOST: Optional[str] = "http://localhost:3001"
    LANGFUSE_PUBLIC_KEY: Optional[str] = "pk-lf-test"
    LANGFUSE_SECRET_KEY: Optional[str] = "sk-lf-test"

    # Tuning — Chunking
    CHUNK_CHILD_TOKENS: int = 250
    CHUNK_PARENT_TOKENS: int = 1500

    # Tuning — Retrieval
    HYBRID_TOP_K: int = 40
    RRF_K: int = 60
    RERANK_TOP_K: int = 8
    RERANK_MIN_SCORE: float = 0.35
    RERANK_BATCH_SIZE: int = 32
    RERANK_TIMEOUT_S: int = 15
    CONTEXT_TOKEN_BUDGET: int = 6000

    # Tuning — Query rewriting
    QUERY_REWRITE_LAST_N_TURNS: int = 6

    # Embedding prefix convention (BGE/E5 style; leave empty for most models)
    EMBEDDING_QUERY_PREFIX: str = ""
    EMBEDDING_DOC_PREFIX: str = ""

    # Legacy alias kept for back-compat with old code referencing LLM_TOP_K_PARENTS
    LLM_TOP_K_PARENTS: int = 8
    RATE_LIMIT_CHAT_PER_HOUR: int = 60

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: object) -> str:
        if isinstance(v, str):
            res = v
            if res.startswith("postgresql://"):
                res = res.replace("postgresql://", "postgresql+asyncpg://", 1)
            # Normalize docker internal hostname to localhost if running on host
            if "@postgres:" in res:
                res = res.replace("@postgres:", "@localhost:", 1)
            return res
        return str(v)

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: object) -> str:
        if isinstance(v, str):
            if "://redis:" in v:
                return v.replace("://redis:", "://localhost:", 1)
            return v
        return str(v)

    @field_validator("QDRANT_URL", mode="before")
    @classmethod
    def assemble_qdrant_url(cls, v: object) -> str:
        if isinstance(v, str):
            if "://qdrant:" in v:
                return v.replace("://qdrant:", "://localhost:", 1)
            return v
        return str(v)

    @field_validator("S3_ENDPOINT_URL", mode="before")
    @classmethod
    def assemble_s3_url(cls, v: object) -> Optional[str]:
        if isinstance(v, str):
            if "://localstack:" in v:
                return v.replace("://localstack:", "://localhost:", 1)
            return v
        return v

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

    @model_validator(mode="after")
    def validate_service_urls(self) -> "Settings":
        """Fail at boot if a required service configuration is missing."""
        if self.LLM_PROVIDER.lower() == "custom" and not self.LLM_BASE_URL:
            raise ValueError("LLM_BASE_URL must be set when LLM_PROVIDER is 'custom'")
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()
