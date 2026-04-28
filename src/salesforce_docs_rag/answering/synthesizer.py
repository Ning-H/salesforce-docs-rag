from salesforce_docs_rag.api.schemas import Citation
from salesforce_docs_rag.config import Settings
from salesforce_docs_rag.models import SearchResult


class AnswerSynthesizer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def answer(self, query: str, results: list[SearchResult]) -> tuple[str, list[Citation]]:
        citations = [
            Citation(
                title=result.title,
                source_url=result.source_url,
                section_path=result.section_path,
            )
            for result in results
        ]
        if not results:
            return (
                "I could not find relevant Salesforce documentation in the current index.",
                citations,
            )
        if self.settings.answer_provider.lower() == "openai":
            return await self._openai_answer(query, results), citations
        return self._local_answer(query, results), citations

    def _local_answer(self, query: str, results: list[SearchResult]) -> str:
        top_sections = []
        for index, result in enumerate(results[:3], start=1):
            section = " > ".join(result.section_path)
            excerpt = self._first_sentences(result.text, max_sentences=3)
            top_sections.append(
                f"{index}. {section}: {excerpt} Source: {result.source_url}"
            )
        return (
            "Based on the retrieved Salesforce documentation, here are the most relevant "
            f"sections for: {query}\n\n" + "\n\n".join(top_sections)
        )

    async def _openai_answer(self, query: str, results: list[SearchResult]) -> str:
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when ANSWER_PROVIDER=openai")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        context = "\n\n".join(
            (
                f"Source {index}\n"
                f"Title: {result.title}\n"
                f"Section: {' > '.join(result.section_path)}\n"
                f"URL: {result.source_url}\n"
                f"Text: {result.text}"
            )
            for index, result in enumerate(results[:5], start=1)
        )
        response = await client.responses.create(
            model=self.settings.openai_chat_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Answer using only the provided Salesforce documentation context. "
                        "If the context is insufficient, say what is missing. Include source "
                        "numbers inline when making factual claims."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {query}\n\nContext:\n{context}",
                },
            ],
        )
        return response.output_text

    @staticmethod
    def _first_sentences(text: str, max_sentences: int) -> str:
        normalized = " ".join(text.split())
        sentences = []
        for part in normalized.split(". "):
            if part:
                sentences.append(part if part.endswith(".") else f"{part}.")
            if len(sentences) >= max_sentences:
                break
        return " ".join(sentences)
