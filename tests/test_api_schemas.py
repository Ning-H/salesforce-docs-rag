import pytest
from pydantic import ValidationError

from salesforce_docs_rag.api.schemas import QueryRequest


def test_query_request_defaults():
    request = QueryRequest(query="SOQL relationship query examples")

    assert request.top_k == 5
    assert request.filters is None


def test_query_request_rejects_large_top_k():
    with pytest.raises(ValidationError):
        QueryRequest(query="SOQL relationship query examples", top_k=100)
