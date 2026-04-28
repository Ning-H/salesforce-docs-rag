PYTHON ?= python3

.PHONY: install test lint api crawl chunk index

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

api:
	$(PYTHON) -m uvicorn salesforce_docs_rag.api.main:app --reload --host 0.0.0.0 --port 8000

crawl:
	$(PYTHON) -m salesforce_docs_rag.ingestion.run_crawl

chunk:
	$(PYTHON) -m salesforce_docs_rag.ingestion.chunk_documents

index:
	$(PYTHON) -m salesforce_docs_rag.ingestion.index_documents
