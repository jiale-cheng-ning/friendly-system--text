import pytest
from core.database import Base, engine, init_db, SessionLocal


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


def test_keyword_match_logistics():
    """Test keyword matching identifies logistics queries."""
    from services.intent_service import keyword_match

    result = keyword_match("我的快递到哪了？什么时候能发货")
    assert result is not None
    assert result["code"] == "C01"


def test_keyword_match_complaint():
    """Test keyword matching identifies complaints."""
    from services.intent_service import keyword_match

    result = keyword_match("我要投诉你们客服态度太差了")
    assert result is not None
    assert result["code"] == "C08"


def test_keyword_match_no_match():
    """Test keyword matching returns None for unrecognized content."""
    from services.intent_service import keyword_match

    result = keyword_match("你好")
    assert result is None


def test_categories_loaded():
    """Test 12 major categories are loaded correctly."""
    from services.intent_service import load_categories

    cats = load_categories()
    assert len(cats) == 12
    codes = [c["code"] for c in cats]
    assert "C01" in codes
    assert "C12" in codes


def test_classify_ticket_keyword_fast_path():
    """Test classification with keyword fast path (no LLM call)."""
    from services.intent_service import classify
    import asyncio

    result = asyncio.run(classify("请问我的快递到哪了 物流信息什么时候更新"))
    assert result.major_code == "C01"
    assert result.route == "auto"
    assert result.confidence > 0.8


def test_classify_human_route():
    """Test that complaint content routes to human."""
    from services.intent_service import classify
    import asyncio

    result = asyncio.run(classify("我要投诉你们卖假货 欺骗消费者"))
    assert result.major_code == "C08"
    assert result.route == "human"
