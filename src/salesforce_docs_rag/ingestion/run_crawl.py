import json
import logging
import sys
import time
from itertools import zip_longest
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from salesforce_docs_rag.config import get_settings
from salesforce_docs_rag.crawler.html_extractor import extract_document
from salesforce_docs_rag.io import write_jsonl
from salesforce_docs_rag.logging import configure_logging
from salesforce_docs_rag.models import RawDocument

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    output_path = Path(settings.raw_docs_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if all("/docs/get_document/" in url for url in settings.crawl_seed_urls):
        count = crawl_salesforce_docs_api(
            seed_urls=settings.crawl_seed_urls,
            output_path=output_path,
            max_pages=settings.max_pages,
        )
        print(f"Wrote {count} raw documents to {output_path}")
        return

    repo_scrapy_path = Path.cwd() / "scrapy_project"
    package_scrapy_path = Path(__file__).resolve().parents[3] / "scrapy_project"
    scrapy_path = repo_scrapy_path if repo_scrapy_path.exists() else package_scrapy_path
    if str(scrapy_path) not in sys.path:
        sys.path.insert(0, str(scrapy_path))
    scrapy_settings = get_project_settings()
    scrapy_settings.set("BOT_NAME", "salesforce_docs_spider")
    scrapy_settings.set("SPIDER_MODULES", ["salesforce_docs_spider.spiders"])
    scrapy_settings.set("TELNETCONSOLE_ENABLED", False)
    scrapy_settings.set(
        "USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    )
    scrapy_settings.set(
        "DEFAULT_REQUEST_HEADERS",
        {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml,"
                "application/json;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    scrapy_settings.set("FEEDS", {str(output_path): {"format": "jsonlines", "overwrite": True}})
    scrapy_settings.set("LOG_LEVEL", settings.log_level)
    process = CrawlerProcess(scrapy_settings)
    process.crawl(
        "salesforce_docs",
        seed_urls=settings.crawl_seed_urls,
        max_pages=settings.max_pages,
    )
    process.start()


def crawl_salesforce_docs_api(seed_urls: list[str], output_path: Path, max_pages: int) -> int:
    documents: list[RawDocument] = []
    seen_pages: set[str] = set()
    guide_payloads = [_fetch_json(guide_url) for guide_url in seed_urls]
    page_groups = [_iter_guide_pages(guide_payload) for guide_payload in guide_payloads]
    guide_by_api_url = {
        page["content_api_url"]: guide_payload
        for guide_payload, pages in zip(guide_payloads, page_groups, strict=True)
        for page in pages
    }

    for page_tuple in zip_longest(*page_groups):
        for page in page_tuple:
            if page is None:
                continue
            if len(documents) >= max_pages:
                return write_jsonl(output_path, documents)
            document = _fetch_page_document(page, guide_by_api_url[page["content_api_url"]])
            if document is None or page["content_api_url"] in seen_pages:
                continue
            seen_pages.add(page["content_api_url"])
            documents.append(document)
            if len(documents) % 25 == 0:
                logger.info("Fetched %s Salesforce documentation pages", len(documents))
    return write_jsonl(output_path, documents)


def _fetch_page_document(page: dict[str, str], guide_payload: dict) -> RawDocument | None:
    try:
        page_payload = _fetch_json(page["content_api_url"])
    except (HTTPError, TimeoutError, URLError) as exc:
        logger.warning(
            "Skipping Salesforce doc page after fetch failure: %s (%s)",
            page["source_url"],
            exc,
        )
        return None

    content = page_payload.get("content") or ""
    title = page_payload.get("title") or page["title"]
    html = f"<main><h1>{title}</h1>{content}</main>"
    document = extract_document(page["source_url"], html)
    if document is None:
        return None

    version = guide_payload.get("version") or {}
    document.release_version = version.get("version_text") or document.release_version
    document.metadata.update(
        {
            "content_document_id": page_payload.get("id") or page["href"],
            "deliverable": guide_payload.get("deliverable"),
            "guide_title": guide_payload.get("doc_title") or guide_payload.get("title"),
            "pdf_url": guide_payload.get("pdf_url"),
        }
    )
    return document


def _fetch_json(url: str, attempts: int = 2, timeout_seconds: int = 10) -> dict:
    last_error: HTTPError | TimeoutError | URLError | None = None
    for attempt in range(1, attempts + 1):
        try:
            with request.urlopen(url, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, TimeoutError, URLError) as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(attempt)
    if last_error is None:
        raise RuntimeError(f"Unable to fetch JSON from {url}")
    raise last_error


def _iter_guide_pages(guide_payload: dict) -> list[dict[str, str]]:
    deliverable = guide_payload["deliverable"]
    version = guide_payload["version"]
    language = guide_payload["language"]
    doc_version = version["doc_version"]
    version_url = version["version_url"]
    locale = language["locale"]

    pages: list[dict[str, str]] = []
    for node in _walk_toc(guide_payload.get("toc") or []):
        href = ((node.get("a_attr") or {}).get("href") or "").split("#", 1)[0]
        if not href or not href.endswith(".htm"):
            continue
        pages.append(
            {
                "title": node.get("text") or href,
                "href": href,
                "content_api_url": (
                    "https://developer.salesforce.com/docs/get_document_content/"
                    f"{deliverable}/{href}/{locale}/{doc_version}"
                ),
                "source_url": urljoin(
                    "https://developer.salesforce.com/",
                    f"docs/{version_url}/{deliverable}/{href}",
                ),
            }
        )
    return pages


def _walk_toc(nodes: list[dict]) -> list[dict]:
    flattened: list[dict] = []
    for node in nodes:
        flattened.append(node)
        flattened.extend(_walk_toc(node.get("children") or []))
    return flattened


if __name__ == "__main__":
    main()
