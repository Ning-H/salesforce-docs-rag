from collections.abc import Iterable
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

import weaviate
from weaviate.classes.config import DataType, Property
from weaviate.classes.query import Filter

from salesforce_docs_rag.models import DocumentChunk, SearchFilters, SearchResult


def _connect(url: str, api_key: str | None = None):
    if "://" not in url and ("weaviate.cloud" in url or "weaviate.network" in url):
        url = f"https://{url}"

    parsed = urlparse(url)
    if api_key and parsed.scheme == "https":
        from weaviate.classes.init import Auth

        return weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=Auth.api_key(api_key),
        )

    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    secure = parsed.scheme == "https"
    if api_key:
        from weaviate.auth import Auth

        return weaviate.connect_to_custom(
            http_host=host,
            http_port=port,
            http_secure=secure,
            grpc_host=host,
            grpc_port=50051,
            grpc_secure=secure,
            auth_credentials=Auth.api_key(api_key),
        )
    return weaviate.connect_to_custom(
        http_host=host,
        http_port=port,
        http_secure=secure,
        grpc_host=host,
        grpc_port=50051,
        grpc_secure=secure,
    )


class WeaviateVectorStore:
    def __init__(self, url: str, collection_name: str, api_key: str | None = None) -> None:
        self.url = url
        self.collection_name = collection_name
        self.api_key = api_key

    def ensure_schema(self) -> None:
        client = _connect(self.url, self.api_key)
        try:
            if client.collections.exists(self.collection_name):
                return
            client.collections.create(
                self.collection_name,
                vectorizer_config=None,
                properties=[
                    Property(name="chunk_id", data_type=DataType.TEXT),
                    Property(name="source_url", data_type=DataType.TEXT),
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="section_path", data_type=DataType.TEXT_ARRAY),
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="doc_type", data_type=DataType.TEXT),
                    Property(name="product_area", data_type=DataType.TEXT),
                    Property(name="release_version", data_type=DataType.TEXT),
                    Property(name="last_updated", data_type=DataType.TEXT),
                ],
            )
        finally:
            client.close()

    def upsert(self, chunks: Iterable[DocumentChunk], vectors: list[list[float]]) -> int:
        self.ensure_schema()
        client = _connect(self.url, self.api_key)
        count = 0
        try:
            collection = client.collections.get(self.collection_name)
            with collection.batch.dynamic() as batch:
                for chunk, vector in zip(chunks, vectors, strict=True):
                    batch.add_object(
                        uuid=uuid5(NAMESPACE_URL, chunk.chunk_id),
                        properties={
                            "chunk_id": chunk.chunk_id,
                            "source_url": str(chunk.source_url),
                            "title": chunk.title,
                            "section_path": chunk.section_path,
                            "text": chunk.text,
                            "doc_type": chunk.doc_type,
                            "product_area": chunk.product_area or "",
                            "release_version": chunk.release_version or "",
                            "last_updated": chunk.last_updated or "",
                        },
                        vector=vector,
                    )
                    count += 1
            return count
        finally:
            client.close()

    def search(
        self, query_vector: list[float], top_k: int, filters: SearchFilters | None = None
    ) -> list[SearchResult]:
        client = _connect(self.url, self.api_key)
        try:
            collection = client.collections.get(self.collection_name)
            where_filter = self._build_filter(filters)
            response = collection.query.near_vector(
                near_vector=query_vector,
                limit=top_k,
                filters=where_filter,
                return_metadata=["distance"],
            )
            results: list[SearchResult] = []
            for item in response.objects:
                props = item.properties
                distance = item.metadata.distance or 0.0
                results.append(
                    SearchResult(
                        chunk_id=str(props["chunk_id"]),
                        score=max(0.0, 1.0 - float(distance)),
                        source_url=str(props["source_url"]),
                        title=str(props["title"]),
                        section_path=list(props.get("section_path") or []),
                        text=str(props["text"]),
                        doc_type=str(props["doc_type"]),
                        product_area=str(props.get("product_area") or "") or None,
                        release_version=str(props.get("release_version") or "") or None,
                    )
                )
            return results
        finally:
            client.close()

    @staticmethod
    def _build_filter(filters: SearchFilters | None):
        if filters is None:
            return None
        clauses = []
        for field in ("doc_type", "product_area", "release_version", "source_url"):
            value = getattr(filters, field)
            if value:
                clauses.append(Filter.by_property(field).equal(value))
        if not clauses:
            return None
        current = clauses[0]
        for clause in clauses[1:]:
            current = current & clause
        return current
