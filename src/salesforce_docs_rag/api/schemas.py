from pydantic import BaseModel, Field

from salesforce_docs_rag.models import SearchFilters, SearchResult


class QueryRequest(BaseModel):
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=25)
    filters: SearchFilters | None = None


class QueryResponse(BaseModel):
    query: str
    results: list[SearchResult]


class HealthResponse(BaseModel):
    status: str
    vector_store: str
    embedding_provider: str
