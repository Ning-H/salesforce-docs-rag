from salesforce_docs_rag.crawler.html_extractor import extract_document


def test_extract_document_keeps_headings_and_metadata():
    html = """
    <html>
      <head><title>Ignored Browser Title</title></head>
      <body>
        <nav>Navigation</nav>
        <main>
          <h1>Data Cloud Identity Resolution</h1>
          <h2>Match Rules</h2>
          <p>Identity resolution helps unify customer profiles across data streams.</p>
          <p>Configure match rules before reconciliation rules.</p>
        </main>
      </body>
    </html>
    """

    url = "https://developer.salesforce.com/docs/data-cloud/identity-resolution"
    document = extract_document(url, html)

    assert document is not None
    assert document.title == "Data Cloud Identity Resolution"
    assert document.product_area == "Data Cloud"
    assert document.doc_type == "developer_docs"
    assert "Match Rules" in document.headings
    assert "Navigation" not in document.text
