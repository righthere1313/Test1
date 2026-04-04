from typing import Any, Dict

from app.services.knowledge_base_service import KnowledgeBaseService


class RAGService:
    def __init__(self) -> None:
        self.kb = KnowledgeBaseService()

    def query(self, query_text: str, k: int = 3) -> Dict[str, Any]:
        answer = self.kb.answer(query_text, k)
        return {
            "query": answer["query"],
            "answer": answer["answer"],
            "sources": answer["citations"],
        }
