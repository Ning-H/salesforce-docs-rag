from salesforce_docs_rag.chunking import chunk_document
from salesforce_docs_rag.config import get_settings
from salesforce_docs_rag.io import read_jsonl, write_jsonl
from salesforce_docs_rag.logging import configure_logging
from salesforce_docs_rag.models import RawDocument


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    chunks = []
    for document in read_jsonl(settings.raw_docs_path, RawDocument):
        chunks.extend(chunk_document(document))
    count = write_jsonl(settings.chunks_path, chunks)
    print(f"Wrote {count} chunks to {settings.chunks_path}")


if __name__ == "__main__":
    main()
