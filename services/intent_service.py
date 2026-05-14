import json
import re
from pathlib import Path
from typing import Optional
from models.intent import ClassificationResult, IntentCategory
from core.llm import llm_client
from core.config import settings

CATEGORIES_PATH = Path(__file__).resolve().parent.parent / "data" / "categories.json"


def load_categories() -> list[dict]:
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["categories"]


def build_categories_text() -> str:
    cats = load_categories()
    lines = []
    for c in cats:
        sub_lines = ", ".join(c["sub_categories"])
        lines.append(f"**{c['code']} {c['name']}** 路由:{c['route']} 优先级:{c['default_priority']}")
        lines.append(f"  子类: {sub_lines}")
        lines.append(f"  关键词: {', '.join(c['keywords'][:6])}")
        lines.append("")
    return "\n".join(lines)


def keyword_match(message: str) -> Optional[dict]:
    """Fast keyword pre-screening before LLM classification."""
    cats = load_categories()
    msg_lower = message.lower()
    best_match = None
    best_score = 0
    for c in cats:
        score = sum(1 for kw in c["keywords"] if kw in msg_lower)
        if score > best_score:
            best_score = score
            best_match = c
    if best_score >= 2:
        return best_match
    return None


async def classify(message: str) -> ClassificationResult:
    """Two-tier classification: keyword pre-screen + LLM fine classification."""
    kw_match = keyword_match(message)
    if kw_match and kw_match["code"] in ["C01", "C05", "C06"]:
        return ClassificationResult(
            major_code=kw_match["code"],
            major_name=kw_match["name"],
            sub_category=kw_match["sub_categories"][0],
            confidence=0.85,
            route=kw_match["route"],
            priority=kw_match["default_priority"],
            reasoning=f"关键词匹配: {kw_match['name']}",
        )

    prompt = load_prompt()
    user_msg = prompt.replace("{CATEGORIES}", build_categories_text()).replace("{USER_MESSAGE}", message)

    result = await llm_client.chat_with_json_output(
        system="你是一个精确的电商工单分类器。严格输出JSON格式的结果。",
        user=user_msg,
        temperature=0.1,
    )

    conf = result.get("confidence", 0.5)
    route = result.get("route", "human")
    priority = result.get("priority", "P2")
    default_route = route
    if conf < 0.65:
        route = "human"

    return ClassificationResult(
        major_code=result.get("major_code", "C12"),
        major_name=result.get("major_name", "其他"),
        sub_category=result.get("sub_category", "其他杂项"),
        confidence=conf,
        route=route,
        priority=priority,
        reasoning=result.get("reasoning", ""),
    )


def load_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "classifier.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def get_category_by_code(code: str) -> Optional[dict]:
    cats = load_categories()
    for c in cats:
        if c["code"] == code:
            return c
    return None
