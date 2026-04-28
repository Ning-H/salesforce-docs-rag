import asyncio

from salesforce_docs_rag.config import get_settings
from salesforce_docs_rag.embeddings import get_embedding_provider
from salesforce_docs_rag.io import read_jsonl
from salesforce_docs_rag.logging import configure_logging
from salesforce_docs_rag.models import DocumentChunk
from salesforce_docs_rag.storage import WeaviateVectorStore


async def index_chunks(batch_size: int = 64) -> int:
    settings = get_settings()
    embedder = get_embedding_provider(settings)
    store = WeaviateVectorStore(
        url=settings.weaviate_url,
        collection_name=settings.weaviate_collection,
        api_key=settings.weaviate_api_key,
    )
    total = 0
    batch: list[DocumentChunk] = []
    for chunk in read_jsonl(settings.chunks_path, DocumentChunk):
        batch.append(chunk)
        if len(batch) >= batch_size:
            vectors = await embedder.embed([item.text for item in batch])
            total += store.upsert(batch, vectors)
            batch = []
    if batch:
        vectors = await embedder.embed([item.text for item in batch])
        total += store.upsert(batch, vectors)
    return total


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    total = asyncio.run(index_chunks())
    print(f"Indexed {total} chunks into {settings.weaviate_collection}")


if __name__ == "__main__":
    main()
