import argparse
import asyncio
import json
from pathlib import Path
from statistics import mean

from salesforce_docs_rag.config import get_settings
from salesforce_docs_rag.embeddings import get_embedding_provider
from salesforce_docs_rag.models import SearchResult
from salesforce_docs_rag.reranking import HybridReranker
from salesforce_docs_rag.storage import WeaviateVectorStore


def load_questions(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def first_relevant_rank(results: list[SearchResult], expected: list[str]) -> int | None:
    for index, result in enumerate(results, start=1):
        if any(fragment in result.source_url for fragment in expected):
            return index
    return None


async def evaluate(
    questions_path: Path,
    top_k: int,
    candidate_k: int,
    use_rerank: bool,
) -> dict:
    settings = get_settings()
    embedder = get_embedding_provider(settings)
    store = WeaviateVectorStore(
        url=settings.weaviate_url,
        collection_name=settings.weaviate_collection,
        api_key=settings.weaviate_api_key,
    )
    reranker = HybridReranker()
    questions = load_questions(questions_path)
    rows = []

    for item in questions:
        query_vector = (await embedder.embed([item["query"]]))[0]
        candidates = store.search(
            query_vector=query_vector,
            top_k=candidate_k if use_rerank else top_k,
        )
        results = reranker.rerank(item["query"], candidates, top_k) if use_rerank else candidates
        rank = first_relevant_rank(results, item["expected_url_contains"])
        rows.append(
            {
                "id": item["id"],
                "query": item["query"],
                "hit": rank is not None,
                "rank": rank,
                "top_result": results[0].source_url if results else None,
            }
        )

    hit_rate = mean(row["hit"] for row in rows) if rows else 0.0
    reciprocal_ranks = [1 / row["rank"] if row["rank"] else 0.0 for row in rows]
    return {
        "embedding_provider": settings.embedding_provider,
        "rerank": use_rerank,
        "top_k": top_k,
        "candidate_k": candidate_k if use_rerank else top_k,
        "hit_rate_at_k": round(hit_rate, 4),
        "mrr_at_k": round(mean(reciprocal_ranks), 4) if reciprocal_ranks else 0.0,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Salesforce docs retrieval quality.")
    parser.add_argument("--questions", type=Path, default=Path("queries/eval_questions.json"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-k", type=int, default=25)
    parser.add_argument("--rerank", action="store_true")
    args = parser.parse_args()

    report = asyncio.run(
        evaluate(
            questions_path=args.questions,
            top_k=args.top_k,
            candidate_k=args.candidate_k,
            use_rerank=args.rerank,
        )
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
