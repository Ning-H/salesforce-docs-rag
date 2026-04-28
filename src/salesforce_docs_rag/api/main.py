from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI

from salesforce_docs_rag.api.dependencies import embedding_provider, vector_store
from salesforce_docs_rag.api.schemas import HealthResponse, QueryRequest, QueryResponse
from salesforce_docs_rag.config import get_settings
from salesforce_docs_rag.embeddings.base import EmbeddingProvider
from salesforce_docs_rag.logging import configure_logging
from salesforce_docs_rag.storage import WeaviateVectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


app = FastAPI(
    title="Salesforce Docs RAG Agent",
    version="0.1.0",
    description="Semantic retrieval over public Salesforce documentation with citations.",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        vector_store="weaviate",
        embedding_provider=settings.embedding_provider,
    )


@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    embedder: Annotated[EmbeddingProvider, Depends(embedding_provider)],
    store: Annotated[WeaviateVectorStore, Depends(vector_store)],
) -> QueryResponse:
    query_vector = (await embedder.embed([request.query]))[0]
    results = store.search(query_vector=query_vector, top_k=request.top_k, filters=request.filters)
    return QueryResponse(query=request.query, results=results)
