import pytest
from pydantic import ValidationError

from salesforce_docs_rag.api.schemas import AnswerRequest, HealthResponse, QueryRequest


def test_query_request_defaults():
    request = QueryRequest(query="SOQL relationship query examples")

    assert request.top_k == 5
    assert request.rerank is False
    assert request.candidate_k is None
    assert request.filters is None


def test_query_request_rejects_large_top_k():
    with pytest.raises(ValidationError):
        QueryRequest(query="SOQL relationship query examples", top_k=100)


def test_answer_request_uses_query_contract():
    request = AnswerRequest(query="How do I write Apex tests?")

    assert request.top_k == 5
    assert request.rerank is True


def test_health_response_includes_answer_provider():
    response = HealthResponse(
        status="ok",
        vector_store="weaviate",
        embedding_provider="local",
        answer_provider="local",
    )

    assert response.answer_provider == "local"
