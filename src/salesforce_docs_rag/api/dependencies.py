from functools import lru_cache

from salesforce_docs_rag.answering import AnswerSynthesizer
from salesforce_docs_rag.config import get_settings
from salesforce_docs_rag.embeddings import get_embedding_provider
from salesforce_docs_rag.storage import WeaviateVectorStore


@lru_cache
def vector_store() -> WeaviateVectorStore:
    settings = get_settings()
    return WeaviateVectorStore(
        url=settings.weaviate_url,
        collection_name=settings.weaviate_collection,
        api_key=settings.weaviate_api_key,
    )


@lru_cache
def embedding_provider():
    return get_embedding_provider(get_settings())


@lru_cache
def answer_synthesizer() -> AnswerSynthesizer:
    return AnswerSynthesizer(get_settings())
