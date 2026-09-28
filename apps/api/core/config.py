import json
from functools import lru_cache
from typing import List, Optional
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: Optional[str] = None

    # Infrastructure
    REDIS_URL: str = "redis://localhost:7379/0"
    CELERY_BROKER_URL: str = "redis://localhost:7379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:7379/2"
    QDRANT_URL: str = "http://localhost:7333"

    # AWS S3 Object Storage
    AWS_REGION: str = Field(default="us-east-1", validation_alias=AliasChoices("AWS_REGION", "AWS_DEFAULT_REGION"))
    AWS_ACCESS_KEY_ID: str = Field(default="test", validation_alias=AliasChoices("AWS_ACCESS_KEY_ID", "AWS_ACCESS_KEY"))
    AWS_SECRET_ACCESS_KEY: str = Field(default="test", validation_alias=AliasChoices("AWS_SECRET_ACCESS_KEY", "AWS_SECRET_KEY"))
    S3_BUCKET_NAME: str = Field(default="srot", validation_alias=AliasChoices("S3_BUCKET_NAME", "BUCKET_NAME", "BUCKET"))
    S3_ENDPOINT_URL: Optional[str] = Field(default=None, validation_alias=AliasChoices("S3_ENDPOINT_URL", "AWS_ENDPOINT_URL"))
    S3_PRESIGNED_EXPIRY_SECONDS: int = 3600

    # Cryptographic Vault
    ENCRYPTION_MASTER_KEY: str
    FLASHRANK_CACHE_DIR: str = "/tmp/flashrank_cache"

    # Runtime
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

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
