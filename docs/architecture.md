# Architecture

The Salesforce Docs RAG Agent has four runtime paths:

1. Crawl: Scrapy starts from configured Salesforce documentation URLs, follows same-domain documentation links, extracts clean text, and writes raw JSONL documents.
2. Chunk: the section chunker splits documents at heading boundaries and prefixes each chunk with the document title and section path.
3. Index: the embedding job batches chunks, calls the configured embedding provider, and upserts vectors plus metadata into Weaviate.
4. Retrieve: FastAPI embeds a natural-language query, executes vector search, applies metadata filters, and returns citation-ready chunks.

The Airflow DAG composes the first three paths as a weekly refresh. For an interview-grade production extension, add sitemap diffing and HTTP `ETag`/`Last-Modified` tracking to index only changed pages.
