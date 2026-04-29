from salesforce_docs_rag.models import SearchResult
from salesforce_docs_rag.reranking import HybridReranker


def _result(chunk_id: str, title: str, section: list[str], text: str, score: float) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id,
        score=score,
        source_url=f"https://example.com/{chunk_id}",
        title=title,
        section_path=section,
        text=text,
        doc_type="developer_docs",
        product_area="Apex",
        release_version="Spring 2026",
    )


def test_hybrid_reranker_promotes_exact_section_match():
    reranker = HybridReranker()
    broad = _result(
        "broad",
        "Learning Apex",
        ["Learning Apex"],
        "Apex tutorials introduce triggers and components.",
        0.25,
    )
    exact = _result(
        "exact",
        "IsTest Annotation",
        ["IsTest Annotation"],
        "Use the IsTest annotation to define Apex test classes and test methods.",
        0.2,
    )

    results = reranker.rerank("How do I write Apex tests?", [broad, exact], top_k=2)

    assert results[0].chunk_id == "exact"
    assert results[0].score > results[1].score
