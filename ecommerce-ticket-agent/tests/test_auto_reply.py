import pytest
from core.database import Base, engine, init_db, SessionLocal


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


def test_auto_reply_closed_detection():
    """Test closed/closure detection in auto-reply output."""
    from agents.auto_reply import AutoReplyAgent
    db = SessionLocal()
    agent = AutoReplyAgent(db)
    db.close()

    assert agent._check_closed("问题是否已解决: 是，客户确认收到退款")
    assert agent._check_closed("已解决，工单闭环")
    assert not agent._check_closed("需要进一步核实客户信息")
    assert not agent._check_closed("请客户提供订单号")


def test_knowledge_search():
    """Test FAQ knowledge base search."""
    from services.knowledge_service import KnowledgeService

    ks = KnowledgeService()
    results = ks.search("物流 发货")
    assert len(results) > 0
    assert any("物流" in r.get("question", "") or "发货" in r.get("question", "") for r in results)

    results = ks.search("退款")
    assert len(results) > 0
    assert any("退款" in r.get("question", "") or "退款" in r.get("answer", "") for r in results)


def test_knowledge_search_by_category():
    """Test FAQ search by category code."""
    from services.knowledge_service import KnowledgeService

    ks = KnowledgeService()
    results = ks.search_by_category("C01")
    assert len(results) > 0
    for r in results:
        assert r["category"] == "C01"


def test_knowledge_no_results():
    """Test search with irrelevant query returns empty."""
    from services.knowledge_service import KnowledgeService

    ks = KnowledgeService()
    results = ks.search("xyz_不存在的查询内容_12345")
    assert len(results) == 0


def test_conversation_memory():
    """Test per-ticket conversation memory."""
    from core.memory import ConversationMemory

    mem = ConversationMemory()
    mem.add(1, "customer", "你好")
    mem.add(1, "agent", "你好，有什么可以帮你的？")
    mem.add(1, "customer", "我的快递到哪了")

    history = mem.get_history(1)
    assert len(history) == 3
    assert history[0]["role"] == "customer"
    assert history[1]["role"] == "agent"

    formatted = mem.get_formatted(1)
    assert "客户" in formatted
    assert "快递" in formatted

    mem.clear(1)
    assert len(mem.get_history(1)) == 0
