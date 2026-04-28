from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="salesforce_docs_weekly_refresh",
    start_date=datetime(2026, 1, 1),
    schedule="@weekly",
    catchup=False,
    tags=["rag", "salesforce", "docs"],
)
def salesforce_docs_weekly_refresh():
    @task
    def crawl_docs() -> None:
        from salesforce_docs_rag.ingestion.run_crawl import main

        main()

    @task
    def chunk_docs() -> None:
        from salesforce_docs_rag.ingestion.chunk_documents import main

        main()

    @task
    def index_docs() -> None:
        from salesforce_docs_rag.ingestion.index_documents import main

        main()

    crawl_docs() >> chunk_docs() >> index_docs()


salesforce_docs_weekly_refresh()
