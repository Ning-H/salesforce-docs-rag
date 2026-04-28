from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    embedding_provider: str = "local"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    answer_provider: str = "local"
    openai_chat_model: str = "gpt-4.1-mini"

    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str | None = None
    weaviate_collection: str = "SalesforceDocChunk"

    raw_docs_path: Path = Path("data/raw/salesforce_docs.jsonl")
    chunks_path: Path = Path("data/processed/salesforce_doc_chunks.jsonl")
    max_pages: int = 200
    crawl_seed_urls: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "https://developer.salesforce.com/docs/get_document/atlas.en-us.apexcode.meta",
            "https://developer.salesforce.com/docs/get_document/atlas.en-us.api_rest.meta",
            "https://developer.salesforce.com/docs/get_document/atlas.en-us.soql_sosl.meta",
        ]
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @field_validator("crawl_seed_urls", mode="before")
    @classmethod
    def split_seed_urls(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
