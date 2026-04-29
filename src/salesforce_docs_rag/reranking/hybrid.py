import math
import re
from collections import Counter

from salesforce_docs_rag.models import SearchResult

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "use",
    "what",
    "when",
    "with",
}


class HybridReranker:
    def rerank(self, query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
        if not results:
            return []

        query_terms = self._tokens(query)
        doc_freq = self._document_frequencies(results)
        total_docs = len(results)
        rescored = [
            (
                self._score_result(
                    result=result,
                    query_terms=query_terms,
                    doc_freq=doc_freq,
                    total_docs=total_docs,
                ),
                result,
            )
            for result in results
        ]
        rescored.sort(key=lambda item: item[0], reverse=True)
        return [
            result.model_copy(update={"score": round(score, 6)})
            for score, result in rescored[:top_k]
        ]

    def _score_result(
        self,
        result: SearchResult,
        query_terms: list[str],
        doc_freq: Counter[str],
        total_docs: int,
    ) -> float:
        text_terms = self._tokens(result.text)
        title_terms = set(self._tokens(result.title))
        section_terms = set(self._tokens(" ".join(result.section_path)))
        product_terms = set(self._tokens(result.product_area or ""))
        text_counts = Counter(text_terms)

        lexical_score = 0.0
        title_bonus = 0.0
        section_bonus = 0.0
        product_bonus = 0.0
        for term in query_terms:
            if text_counts[term]:
                idf = math.log((1 + total_docs) / (1 + doc_freq[term])) + 1
                lexical_score += (1 + math.log(text_counts[term])) * idf
            if term in title_terms:
                title_bonus += 1.5
            if term in section_terms:
                section_bonus += 1.0
            if term in product_terms:
                product_bonus += 0.5

        query_len = max(1, len(query_terms))
        lexical_score = lexical_score / query_len
        metadata_score = (title_bonus + section_bonus + product_bonus) / query_len
        return (result.score * 3.0) + (lexical_score * 0.35) + (metadata_score * 0.7)

    @staticmethod
    def _document_frequencies(results: list[SearchResult]) -> Counter[str]:
        doc_freq: Counter[str] = Counter()
        for result in results:
            doc_freq.update(set(HybridReranker._tokens(result.text)))
        return doc_freq

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [
            HybridReranker._normalize_token(token)
            for token in TOKEN_PATTERN.findall(text)
            if HybridReranker._normalize_token(token) not in STOPWORDS
        ]

    @staticmethod
    def _normalize_token(token: str) -> str:
        token = token.lower()
        if token == "istest":
            return "test"
        if token in {"authenticate", "authentication", "authorization", "authorize", "oauth"}:
            return "auth"
        if len(token) > 3 and token.endswith("s"):
            return token[:-1]
        return token
