from salesforce_docs_rag.crawler.classification import classify_doc_type, infer_release_version


def test_classifies_salesforce_doc_types():
    trailhead_url = "https://trailhead.salesforce.com/content/learn/modules/x"
    help_url = "https://help.salesforce.com/s/articleView?id=release-notes.rn.htm"

    assert classify_doc_type(trailhead_url) == "trailhead"
    assert classify_doc_type("https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta") == (
        "developer_docs"
    )
    assert classify_doc_type(help_url) == "release_notes"


def test_infers_release_version():
    assert infer_release_version("", "Spring '26 Release Notes", "") == "Spring 2026"
