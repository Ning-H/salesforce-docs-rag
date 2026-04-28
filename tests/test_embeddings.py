import pytest

from salesforce_docs_rag.embeddings import LocalHashEmbeddingProvider


@pytest.mark.asyncio
async def test_local_embeddings_are_deterministic_and_normalized():
    provider = LocalHashEmbeddingProvider(dimensions=32)

    first = (await provider.embed(["Data Cloud identity resolution"]))[0]
    second = (await provider.embed(["Data Cloud identity resolution"]))[0]

    assert first == second
    assert len(first) == 32
    assert sum(value * value for value in first) == pytest.approx(1.0)
