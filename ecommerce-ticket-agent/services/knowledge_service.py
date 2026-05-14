import json
from pathlib import Path
from typing import List
from models.knowledge import KnowledgeEntry

FAQ_PATH = Path(__file__).resolve().parent.parent / "data" / "faq_samples.json"


class KnowledgeService:
    def __init__(self):
        self._entries: List[dict] = []
        self._load_faq()

    def _load_faq(self):
        if FAQ_PATH.exists():
            with open(FAQ_PATH, "r", encoding="utf-8") as f:
                self._entries = json.load(f)

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Simple keyword-based search (ChromaDB optional upgrade)."""
        query_lower = query.lower()
        scored = []
        for entry in self._entries:
            score = 0
            q = entry.get("question", "").lower()
            answer = entry.get("answer", "").lower()
            tags = " ".join(entry.get("tags", [])).lower()
            if query_lower in q or any(w in query_lower for w in q.split()):
                score += 5
            for kw in query_lower.split():
                if kw in q:
                    score += 3
                if kw in answer:
                    score += 1
                if kw in tags:
                    score += 2
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

    def search_by_category(self, category_code: str) -> List[dict]:
        return [e for e in self._entries if e.get("category") == category_code]

    def format_results(self, results: List[dict]) -> str:
        if not results:
            return "（未找到相关FAQ条目）"
        lines = []
        for r in results:
            lines.append(f"Q: {r['question']}")
            lines.append(f"A: {r['answer']}")
            lines.append("---")
        return "\n".join(lines)

    def add_entry(self, entry: KnowledgeEntry):
        data = {
            "id": entry.id,
            "question": entry.question,
            "answer": entry.answer,
            "category": entry.category,
            "tags": entry.tags,
        }
        self._entries.append(data)
        with open(FAQ_PATH, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, ensure_ascii=False, indent=2)


knowledge_service = KnowledgeService()
