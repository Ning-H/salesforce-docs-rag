FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY scrapy_project ./scrapy_project
COPY dags ./dags

RUN pip install --no-cache-dir ".[dev,airflow]"

EXPOSE 8000
CMD ["uvicorn", "salesforce_docs_rag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
