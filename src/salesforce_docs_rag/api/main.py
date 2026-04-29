from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI

from salesforce_docs_rag.answering import AnswerSynthesizer
from salesforce_docs_rag.api.dependencies import (
    answer_synthesizer,
    embedding_provider,
    hybrid_reranker,
    vector_store,
)
from salesforce_docs_rag.api.schemas import (
    AnswerRequest,
    AnswerResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
)
from salesforce_docs_rag.config import get_settings
from salesforce_docs_rag.embeddings.base import EmbeddingProvider
from salesforce_docs_rag.logging import configure_logging
from salesforce_docs_rag.models import SearchResult
from salesforce_docs_rag.reranking import HybridReranker
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
        answer_provider=settings.answer_provider,
    )


@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    embedder: Annotated[EmbeddingProvider, Depends(embedding_provider)],
    store: Annotated[WeaviateVectorStore, Depends(vector_store)],
    reranker: Annotated[HybridReranker, Depends(hybrid_reranker)],
) -> QueryResponse:
    results = await retrieve_results(request, embedder, store, reranker)
    return QueryResponse(query=request.query, results=results)


@app.post("/answer", response_model=AnswerResponse)
async def answer(
    request: AnswerRequest,
    embedder: Annotated[EmbeddingProvider, Depends(embedding_provider)],
    store: Annotated[WeaviateVectorStore, Depends(vector_store)],
    synthesizer: Annotated[AnswerSynthesizer, Depends(answer_synthesizer)],
    reranker: Annotated[HybridReranker, Depends(hybrid_reranker)],
) -> AnswerResponse:
    results = await retrieve_results(request, embedder, store, reranker)
    answer_text, citations = await synthesizer.answer(request.query, results)
    return AnswerResponse(
        query=request.query,
        answer=answer_text,
        citations=citations,
        retrieved_results=results,
    )


async def retrieve_results(
    request: QueryRequest,
    embedder: EmbeddingProvider,
    store: WeaviateVectorStore,
    reranker: HybridReranker,
) -> list[SearchResult]:
    query_vector = (await embedder.embed([request.query]))[0]
    candidate_k = request.candidate_k or (min(100, max(request.top_k, request.top_k * 4)))
    candidates = store.search(
        query_vector=query_vector,
        top_k=candidate_k if request.rerank else request.top_k,
        filters=request.filters,
    )
    if request.rerank:
        return reranker.rerank(request.query, candidates, top_k=request.top_k)
    return candidates
