import json
from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str

    # Infrastructure
    REDIS_URL: str = "redis://localhost:7379/0"
    QDRANT_URL: str = "http://localhost:7333"

    # Cryptographic Vault
    ENCRYPTION_MASTER_KEY: str


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
