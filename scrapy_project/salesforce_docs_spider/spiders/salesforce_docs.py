import json
from urllib.parse import urljoin, urlparse

import scrapy

from salesforce_docs_rag.crawler.html_extractor import extract_document
from salesforce_docs_rag.models import RawDocument


class SalesforceDocsSpider(scrapy.Spider):
    name = "salesforce_docs"
    allowed_domains = [
        "developer.salesforce.com",
        "help.salesforce.com",
        "trailhead.salesforce.com",
    ]

    def __init__(self, seed_urls: list[str] | None = None, max_pages: int = 200, **kwargs):
        super().__init__(**kwargs)
        self.seed_urls = seed_urls or ["https://developer.salesforce.com/docs"]
        self.max_pages = int(max_pages)
        self.pages_seen = 0
        self.items_seen = 0

    def start_requests(self):
        for url in self.seed_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.items_seen >= self.max_pages:
            return
        self.pages_seen += 1

        if "/docs/get_document/" in response.url:
            yield from self._parse_docs_api(response)
            return

        api_url = self._docs_api_url(response.url)
        if api_url:
            yield scrapy.Request(api_url, callback=self.parse)
            return

        document = extract_document(response.url, response.text)
        if document is not None:
            self.items_seen += 1
            yield document.model_dump(mode="json")

        for href in response.css("a::attr(href)").getall():
            if self.items_seen >= self.max_pages:
                break
            next_url = urljoin(response.url, href)
            if self._should_follow(next_url):
                yield scrapy.Request(next_url, callback=self.parse)

    def _parse_docs_api(self, response):
        try:
            payload = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning("Skipping non-JSON docs API response: %s", response.url)
            return

        content = payload.get("content") or ""
        title = payload.get("title") or payload.get("doc_title") or "Salesforce Documentation"
        if content:
            document = self._document_from_api_payload(response.url, title, content, payload)
            if document is not None:
                self.items_seen += 1
                yield document.model_dump(mode="json")

        # The docs API guide response includes a full table of contents. The guide-level
        # payload is enough for a non-empty starter crawl; later phases can fan out into
        # get_document_content endpoints for every TOC entry.
        if self.items_seen >= self.max_pages:
            return

    def _document_from_api_payload(
        self, url: str, title: str, content: str, payload: dict
    ) -> RawDocument | None:
        html = f"<main><h1>{title}</h1>{content}</main>"
        document = extract_document(url, html)
        if document is None:
            return None
        version = payload.get("version") or {}
        document.release_version = version.get("version_text") or document.release_version
        document.metadata.update(
            {
                "content_document_id": payload.get("content_document_id"),
                "deliverable": payload.get("deliverable"),
                "pdf_url": payload.get("pdf_url"),
            }
        )
        return document

    def _should_follow(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if parsed.netloc not in self.allowed_domains:
            return False
        lower = url.lower()
        return any(
            marker in lower
            for marker in (
                "/docs",
                "/docs/get_document/",
                "release-notes",
                "trailhead.salesforce.com/content/learn",
                "help.salesforce.com/s/articleview",
            )
        )

    @staticmethod
    def _docs_api_url(url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.netloc != "developer.salesforce.com":
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "docs" and parts[1].startswith("atlas."):
            return f"https://developer.salesforce.com/docs/get_document/{parts[1]}"
        return None
