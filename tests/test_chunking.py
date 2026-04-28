from salesforce_docs_rag.chunking import chunk_document
from salesforce_docs_rag.models import RawDocument


def test_chunk_document_splits_by_heading():
    document = RawDocument(
        url="https://developer.salesforce.com/docs/example",
        title="Apex Developer Guide",
        headings=["Apex Developer Guide", "Batch Apex", "Governor Limits"],
        doc_type="developer_docs",
        product_area="Apex",
        text="\n".join(
            [
                "Apex Developer Guide",
                "Batch Apex",
                "Use Batch Apex for long-running jobs over many records.",
                "Governor Limits",
                "Batch jobs have limits for heap, CPU, and database operations.",
            ]
        ),
    )

    chunks = chunk_document(document)

    assert len(chunks) == 2
    assert chunks[0].section_path == ["Apex Developer Guide", "Batch Apex"]
    assert chunks[1].section_path == ["Apex Developer Guide", "Governor Limits"]
    assert chunks[0].chunk_id != chunks[1].chunk_id
