from salesforce_docs_rag.config import Settings
from salesforce_docs_rag.embeddings.base import EmbeddingProvider
from salesforce_docs_rag.embeddings.local import LocalHashEmbeddingProvider
from salesforce_docs_rag.embeddings.openai_provider import OpenAIEmbeddingProvider


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider.lower() == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            dimensions=settings.embedding_dimensions,
        )
    return LocalHashEmbeddingProvider(dimensions=settings.embedding_dimensions)
