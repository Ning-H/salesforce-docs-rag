from urllib.parse import urlparse

PRODUCT_KEYWORDS = {
    "data cloud": ("data-cloud", "datacloud", "customer-data-platform", "identity-resolution"),
    "agentforce": ("agentforce", "einstein-bot", "copilot"),
    "apex": ("apex", "apexcode", "apex_classes"),
    "rest api": ("api_rest", "rest_api", "rest-api"),
    "soql": ("soql", "query-language"),
    "trailhead": ("trailhead", "modules", "content/learn"),
}


def classify_doc_type(url: str) -> str:
    parsed = urlparse(url)
    lower = url.lower()
    if "trailhead.salesforce.com" in parsed.netloc:
        return "trailhead"
    if "release-notes" in lower or "rn_" in lower:
        return "release_notes"
    if "developer.salesforce.com/docs" in lower:
        return "developer_docs"
    if "help.salesforce.com" in lower:
        return "help_docs"
    return "docs"


def infer_product_area(url: str, title: str, headings: list[str] | None = None) -> str | None:
    haystack = " ".join([url, title, *(headings or [])]).lower()
    for product, keywords in PRODUCT_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return product.title()
    return None


def infer_release_version(url: str, title: str, text: str) -> str | None:
    haystack = " ".join([url, title, text[:500]]).lower()
    for season in ("spring", "summer", "winter"):
        marker = f"{season} '"
        index = haystack.find(marker)
        if index != -1 and index + len(marker) + 2 <= len(haystack):
            year = haystack[index + len(marker) : index + len(marker) + 2]
            if year.isdigit():
                return f"{season.title()} 20{year}"
    return None
