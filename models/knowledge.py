from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KnowledgeEntry:
    id: str
    question: str
    answer: str
    category: str
    tags: list[str]
    created_at: Optional[datetime] = None
