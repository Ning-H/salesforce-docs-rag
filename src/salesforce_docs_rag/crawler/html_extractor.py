from bs4 import BeautifulSoup

from salesforce_docs_rag.crawler.classification import (
    classify_doc_type,
    infer_product_area,
    infer_release_version,
)
from salesforce_docs_rag.models import RawDocument


def clean_text(value: str) -> str:
    return " ".join(value.split())


def extract_document(url: str, html: str) -> RawDocument | None:
    soup = BeautifulSoup(html, "lxml")
    for element in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        element.decompose()

    title = clean_text(
        (soup.find("h1") or soup.find("title") or soup.new_tag("title")).get_text(" ", strip=True)
    )
    content_root = soup.find("main") or soup.find("article") or soup.body or soup
    headings = [
        clean_text(node.get_text(" ", strip=True))
        for node in content_root.find_all(["h1", "h2", "h3"])
        if clean_text(node.get_text(" ", strip=True))
    ]
    paragraphs = [
        clean_text(node.get_text(" ", strip=True))
        for node in content_root.find_all(["h1", "h2", "h3", "p", "li", "pre", "code"])
    ]
    text = "\n".join(item for item in paragraphs if item)
    if not title or len(text) < 100:
        return None

    doc_type = classify_doc_type(url)
    product_area = infer_product_area(url, title, headings)
    release_version = infer_release_version(url, title, text)
    return RawDocument(
        url=url,
        title=title,
        text=text,
        headings=headings,
        doc_type=doc_type,
        product_area=product_area,
        release_version=release_version,
    )
