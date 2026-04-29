import asyncio
import os
from typing import Any

import requests
import streamlit as st

from salesforce_docs_rag.answering import AnswerSynthesizer
from salesforce_docs_rag.api.schemas import AnswerRequest
from salesforce_docs_rag.config import Settings
from salesforce_docs_rag.embeddings import get_embedding_provider
from salesforce_docs_rag.reranking import HybridReranker
from salesforce_docs_rag.storage import WeaviateVectorStore

API_BASE_URL = os.getenv("RAG_API_BASE_URL")
EXAMPLE_QUERIES = [
    "How do I write Apex tests?",
    "How do I authenticate to the Salesforce REST API?",
    "When should I use SOQL versus SOSL?",
    "What data types and collections does Apex support?",
]


def secret_or_env(name: str, default: str | None = None) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value) if value not in (None, "") else os.getenv(name, default)


def direct_settings() -> Settings:
    values: dict[str, Any] = {}
    secret_fields = {
        "EMBEDDING_PROVIDER": "embedding_provider",
        "ANSWER_PROVIDER": "answer_provider",
        "OPENAI_API_KEY": "openai_api_key",
        "OPENAI_EMBEDDING_MODEL": "openai_embedding_model",
        "OPENAI_CHAT_MODEL": "openai_chat_model",
        "WEAVIATE_URL": "weaviate_url",
        "WEAVIATE_API_KEY": "weaviate_api_key",
        "WEAVIATE_COLLECTION": "weaviate_collection",
    }
    for secret_name, field_name in secret_fields.items():
        value = secret_or_env(secret_name)
        if value:
            values[field_name] = value

    dimensions = secret_or_env("EMBEDDING_DIMENSIONS")
    if dimensions:
        values["embedding_dimensions"] = int(dimensions)

    return Settings(**values)


def call_answer_api(payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}/answer", json=payload, timeout=90)
    response.raise_for_status()
    return response.json()


def call_health_api() -> dict[str, Any] | None:
    if not API_BASE_URL:
        settings = direct_settings()
        return {
            "status": "ok",
            "vector_store": "weaviate",
            "embedding_provider": settings.embedding_provider,
            "answer_provider": settings.answer_provider,
        }
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


async def answer_direct(request: AnswerRequest) -> dict[str, Any]:
    settings = direct_settings()
    embedder = get_embedding_provider(settings)
    store = WeaviateVectorStore(
        url=settings.weaviate_url,
        collection_name=settings.weaviate_collection,
        api_key=settings.weaviate_api_key,
    )
    reranker = HybridReranker()
    synthesizer = AnswerSynthesizer(settings)

    query_vector = (await embedder.embed([request.query]))[0]
    candidate_k = request.candidate_k or min(100, max(request.top_k, request.top_k * 4))
    candidates = store.search(
        query_vector=query_vector,
        top_k=candidate_k if request.rerank else request.top_k,
        filters=request.filters,
    )
    if request.rerank:
        results = reranker.rerank(request.query, candidates, top_k=request.top_k)
    else:
        results = candidates
    answer_text, citations = await synthesizer.answer(request.query, results)
    return {
        "query": request.query,
        "answer": answer_text,
        "citations": [citation.model_dump() for citation in citations],
        "retrieved_results": [result.model_dump() for result in results],
    }


def answer_question(payload: dict[str, Any]) -> dict[str, Any]:
    if API_BASE_URL:
        return call_answer_api(payload)
    return asyncio.run(answer_direct(AnswerRequest(**payload)))


def main() -> None:
    st.set_page_config(page_title="Salesforce Docs RAG", layout="wide")

    st.title("Salesforce Docs RAG")
    st.caption("Grounded answers over indexed Salesforce documentation.")

    with st.sidebar:
        st.subheader("Retrieval")
        top_k = st.slider("Results", min_value=1, max_value=10, value=5)
        rerank = st.toggle("Hybrid rerank", value=True)
        candidate_k = st.slider(
            "Candidates",
            min_value=top_k,
            max_value=50,
            value=max(25, top_k),
        )
        st.divider()
        health = call_health_api()
        if health:
            st.metric("Mode", "FastAPI" if API_BASE_URL else "Direct")
            st.metric("Embeddings", health["embedding_provider"])
            st.metric("Answers", health["answer_provider"])
        else:
            st.error("FastAPI is not reachable.")

    selected_example = st.selectbox("Example questions", EXAMPLE_QUERIES)
    query = st.text_area("Question", value=selected_example, height=90)

    submitted = st.button("Ask", type="primary", disabled=not query.strip())

    if submitted:
        payload = {
            "query": query.strip(),
            "top_k": top_k,
            "candidate_k": candidate_k,
            "rerank": rerank,
        }
        with st.spinner("Retrieving Salesforce docs and generating a grounded answer..."):
            try:
                data = answer_question(payload)
            except (requests.RequestException, ValueError) as exc:
                st.error(f"Request failed: {exc}")
                st.stop()

        st.subheader("Answer")
        st.markdown(data["answer"])

        st.subheader("Citations")
        for index, citation in enumerate(data["citations"], start=1):
            section = " > ".join(citation["section_path"])
            st.markdown(f"{index}. [{citation['title']}]({citation['source_url']})")
            if section:
                st.caption(section)

        st.subheader("Retrieved Chunks")
        for index, result in enumerate(data["retrieved_results"], start=1):
            label = f"{index}. {result['title']}  |  score {result['score']:.4f}"
            with st.expander(label):
                st.markdown(f"[Source]({result['source_url']})")
                st.caption(" > ".join(result["section_path"]))
                st.write(result["text"])
    else:
        st.info("Ask a question to retrieve Salesforce documentation and generate a cited answer.")


if __name__ == "__main__":
    main()
