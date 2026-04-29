from __future__ import annotations

from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task


def _count_jsonl(path: str | Path) -> int:
    file_path = Path(path)
    if not file_path.exists():
        return 0
    with file_path.open(encoding="utf-8") as file:
        return sum(1 for _ in file)


@dag(
    dag_id="salesforce_docs_weekly_refresh",
    start_date=datetime(2026, 1, 1),
    schedule="@weekly",
    catchup=False,
    max_active_runs=1,
    tags=["rag", "salesforce", "docs"],
)
def salesforce_docs_weekly_refresh():
    @task
    def crawl_docs() -> dict[str, int | str]:
        from salesforce_docs_rag.config import get_settings
        from salesforce_docs_rag.ingestion.run_crawl import main

        main()
        settings = get_settings()
        return {
            "stage": "crawl",
            "raw_docs": _count_jsonl(settings.raw_docs_path),
            "path": str(settings.raw_docs_path),
        }

    @task
    def chunk_docs() -> dict[str, int | str]:
        from salesforce_docs_rag.config import get_settings
        from salesforce_docs_rag.ingestion.chunk_documents import main

        main()
        settings = get_settings()
        return {
            "stage": "chunk",
            "chunks": _count_jsonl(settings.chunks_path),
            "path": str(settings.chunks_path),
        }

    @task
    def index_docs() -> dict[str, int | str]:
        import asyncio

        from salesforce_docs_rag.config import get_settings
        from salesforce_docs_rag.ingestion.index_documents import index_chunks

        settings = get_settings()
        indexed = asyncio.run(index_chunks())
        return {
            "stage": "index",
            "indexed_chunks": indexed,
            "collection": settings.weaviate_collection,
        }

    @task
    def summarize_refresh(
        crawl_summary: dict[str, int | str],
        chunk_summary: dict[str, int | str],
        index_summary: dict[str, int | str],
    ) -> dict[str, int | str]:
        summary = {
            "raw_docs": crawl_summary["raw_docs"],
            "chunks": chunk_summary["chunks"],
            "indexed_chunks": index_summary["indexed_chunks"],
            "collection": index_summary["collection"],
        }
        print(f"Salesforce docs refresh summary: {summary}")
        return summary

    crawl_summary = crawl_docs()
    chunk_summary = chunk_docs()
    index_summary = index_docs()

    crawl_summary >> chunk_summary >> index_summary
    summarize_refresh(crawl_summary, chunk_summary, index_summary)


salesforce_docs_weekly_refresh()
