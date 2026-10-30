from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://rag:rag@db:5432/rag"
    redis_url: str = "redis://redis:6379/0"
    dev_token: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    provider: str = "offline"
    storage: str = "local"
    storage_path: str = "/data/originals"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    aws_region: str = "us-east-1"
    pinecone_api_key: str = ""
    pinecone_index: str = "knowledge"
    pinecone_host: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    openai_api_key: str = ""
    chat_model: str = ""
    max_upload_bytes: int = 20 * 1024 * 1024
    max_text_chars: int = 500_000
    max_context_chars: int = 16000
    run_timeout: int = 45
    cors_origin: str = "http://localhost:3000"
    scan_mode: str = "disabled"
    clamd_host: str = "clamav"
    clamd_port: int = 3310
    scan_timeout: int = Field(default=30, ge=1, le=120)
    parser_timeout: int = Field(default=20, ge=1, le=120)
    parser_memory_mb: int = Field(default=512, ge=128, le=2048)
    upload_timeout: int = Field(default=30, ge=1, le=120)

    @model_validator(mode="after")
    def secure_modes(self):
        if self.scan_mode not in {"disabled", "clamav"}:
            raise ValueError("Unknown scanner mode")
        if self.storage == "s3" and not self.s3_bucket:
            raise ValueError("S3 bucket is required")
        if self.provider not in {"offline", "live"} or self.storage not in {"local", "s3"}:
            raise ValueError("Unknown adapter mode")
        if self.environment != "development":
            if self.scan_mode != "clamav":
                raise ValueError("Non-development environments require malware scanning")
            if self.dev_token or self.provider != "live" or self.storage != "s3":
                raise ValueError("Production requires OIDC, live providers and S3")
            if not all([self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url]):
                raise ValueError("OIDC configuration is required")
        if self.provider == "live" and not all(
            [self.openai_api_key, self.chat_model, self.pinecone_api_key, self.pinecone_host]
        ):
            raise ValueError("Live provider configuration is incomplete")
        return self


@lru_cache
def settings():
    return Settings()
