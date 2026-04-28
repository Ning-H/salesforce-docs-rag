from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class RawDocument(BaseModel):
    url: HttpUrl
    title: str
    text: str
    headings: list[str] = Field(default_factory=list)
    doc_type: str = "docs"
    product_area: str | None = None
    release_version: str | None = None
    last_updated: str | None = None
    crawled_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    chunk_id: str
    source_url: HttpUrl
    title: str
    section_path: list[str]
    text: str
    doc_type: str
    product_area: str | None = None
    release_version: str | None = None
    last_updated: str | None = None
    token_estimate: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchFilters(BaseModel):
    doc_type: str | None = None
    product_area: str | None = None
    release_version: str | None = None
    source_url: str | None = None


class SearchResult(BaseModel):
    chunk_id: str
    score: float
    source_url: str
    title: str
    section_path: list[str]
    text: str
    doc_type: str
    product_area: str | None = None
    release_version: str | None = None
