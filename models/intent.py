from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IntentCategory:
    code: str
    name: str
    sub_categories: list[str]
    route: str  # "auto" / "semi" / "human"
    priority: str  # P0-P3
    keywords: list[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    major_code: str
    major_name: str
    sub_category: str
    confidence: float
    route: str
    priority: str
    reasoning: str
