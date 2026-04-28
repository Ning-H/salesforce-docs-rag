import pytest

from salesforce_docs_rag.answering import AnswerSynthesizer
from salesforce_docs_rag.config import Settings
from salesforce_docs_rag.models import SearchResult


@pytest.mark.asyncio
async def test_local_answer_includes_citations_and_retrieved_context():
    synthesizer = AnswerSynthesizer(Settings(answer_provider="local"))
    result = SearchResult(
        chunk_id="chunk-1",
        score=0.9,
        source_url="https://developer.salesforce.com/docs/example",
        title="Apex Testing",
        section_path=["Apex Testing", "Unit Tests"],
        text="Apex tests validate Apex code. Test methods do not commit data.",
        doc_type="developer_docs",
        product_area="Apex",
        release_version="Spring 2026",
    )

    answer, citations = await synthesizer.answer("How do I write Apex tests?", [result])

    assert "Apex Testing > Unit Tests" in answer
    assert "https://developer.salesforce.com/docs/example" in answer
    assert citations[0].title == "Apex Testing"
