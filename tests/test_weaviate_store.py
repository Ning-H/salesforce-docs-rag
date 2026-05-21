from salesforce_docs_rag.storage.weaviate_store import _normalize_weaviate_url


def test_normalize_weaviate_cloud_url_keeps_only_cluster_host():
    url, is_cloud = _normalize_weaviate_url(
        "https://abc123.us-east1.gcp.weaviate.cloud/v1/meta"
    )

    assert url == "abc123.us-east1.gcp.weaviate.cloud"
    assert is_cloud is True


def test_normalize_weaviate_cloud_hostname_adds_cloud_detection():
    url, is_cloud = _normalize_weaviate_url("abc123.weaviate.network")

    assert url == "abc123.weaviate.network"
    assert is_cloud is True


def test_normalize_custom_url_preserves_scheme_and_port():
    url, is_cloud = _normalize_weaviate_url("http://localhost:8080")

    assert url == "http://localhost:8080"
    assert is_cloud is False
