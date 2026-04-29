from pydantic import BaseModel, Field

from salesforce_docs_rag.models import SearchFilters, SearchResult


class QueryRequest(BaseModel):
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=25)
    candidate_k: int | None = Field(default=None, ge=1, le=100)
    rerank: bool = False
    filters: SearchFilters | None = None


class QueryResponse(BaseModel):
    query: str
    results: list[SearchResult]


class Citation(BaseModel):
    title: str
    source_url: str
    section_path: list[str]


class AnswerRequest(QueryRequest):
    rerank: bool = True


class AnswerResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    retrieved_results: list[SearchResult]


class HealthResponse(BaseModel):
    status: str
    vector_store: str
    embedding_provider: str
    answer_provider: str
