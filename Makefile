PYTHON ?= python3

.PHONY: install test lint api crawl chunk index ui airflow-init airflow-up airflow-down airflow-logs

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

ui:
	RAG_API_BASE_URL=http://localhost:8000 $(PYTHON) -m streamlit run streamlit_app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

airflow-init:
	docker compose up airflow-init

airflow-up:
	docker compose up -d airflow-webserver airflow-scheduler

airflow-down:
	docker compose stop airflow-webserver airflow-scheduler airflow-postgres

airflow-logs:
	docker compose logs -f airflow-scheduler airflow-webserver
