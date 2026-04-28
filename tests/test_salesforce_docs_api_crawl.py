from salesforce_docs_rag.ingestion.run_crawl import _iter_guide_pages


def test_iter_guide_pages_builds_content_and_source_urls():
    guide_payload = {
        "deliverable": "apexcode",
        "version": {
            "doc_version": "260.0",
            "version_url": "atlas.en-us.apexcode.meta",
        },
        "language": {"locale": "en-us"},
        "toc": [
            {
                "text": "Apex Developer Guide",
                "a_attr": {"href": "apex_dev_guide.htm"},
                "children": [
                    {
                        "text": "Introducing Apex",
                        "a_attr": {"href": "apex_intro.htm#anchor"},
                        "children": [],
                    }
                ],
            }
        ],
    }

    pages = _iter_guide_pages(guide_payload)

    assert pages[0]["content_api_url"] == (
        "https://developer.salesforce.com/docs/get_document_content/"
        "apexcode/apex_dev_guide.htm/en-us/260.0"
    )
    assert pages[1]["source_url"] == (
        "https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/"
        "apexcode/apex_intro.htm"
    )
