import hashlib

from salesforce_docs_rag.models import DocumentChunk, RawDocument

HEADING_PREFIXES = ("# ", "## ", "### ")


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) * 4 // 3)


def _chunk_id(url: str, section_path: list[str], ordinal: int, text: str) -> str:
    digest = hashlib.sha256(f"{url}|{section_path}|{ordinal}|{text[:200]}".encode()).hexdigest()
    return digest[:24]


def chunk_document(document: RawDocument, max_tokens: int = 650) -> list[DocumentChunk]:
    """Split a document by heading-like lines while keeping section context."""
    current_path: list[str] = [document.title]
    current_lines: list[str] = []
    chunks: list[DocumentChunk] = []
    ordinal = 0

    def flush() -> None:
        nonlocal ordinal, current_lines
        body = "\n".join(line for line in current_lines if line.strip()).strip()
        if not body:
            current_lines = []
            return
        prefixed = "\n".join([*current_path, body])
        chunks.append(
            DocumentChunk(
                chunk_id=_chunk_id(str(document.url), current_path, ordinal, prefixed),
                source_url=document.url,
                title=document.title,
                section_path=current_path.copy(),
                text=prefixed,
                doc_type=document.doc_type,
                product_area=document.product_area,
                release_version=document.release_version,
                last_updated=document.last_updated,
                token_estimate=estimate_tokens(prefixed),
                metadata=document.metadata,
            )
        )
        ordinal += 1
        current_lines = []

    for raw_line in document.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line in document.headings and len(line.split()) <= 16:
            flush()
            if line != document.title:
                current_path = [document.title, line]
            continue
        current_lines.append(line)
        if estimate_tokens("\n".join([*current_path, *current_lines])) >= max_tokens:
            flush()

    flush()
    return chunks


def chunk_documents(documents: list[RawDocument], max_tokens: int = 650) -> list[DocumentChunk]:
    return [
        chunk
        for document in documents
        for chunk in chunk_document(document, max_tokens=max_tokens)
    ]
