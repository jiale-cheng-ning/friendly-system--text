import pytest
from core.database import SessionLocal, init_db, engine, Base


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_ticket_from_manual():
    """Test ticket creation via reception agent with manual channel."""
    db = SessionLocal()
    from agents.reception import ReceptionAgent
    from models.ticket import TicketStatus

    agent = ReceptionAgent(db)
    import asyncio
    ticket = asyncio.run(agent.receive_from_channel("manual", {
        "customer_name": "测试用户",
        "customer_id": "test_001",
        "title": "物流查询测试",
        "content": "我的订单什么时候到货？",
    }))
    db.close()

    assert ticket is not None
    assert ticket.customer_name == "测试用户"
    assert ticket.channel == "manual"
    assert ticket.status == TicketStatus.NEW.value
    assert ticket.title == "物流查询测试"


def test_duplicate_detection():
    """Test that duplicate tickets within 1 hour are rejected."""
    db = SessionLocal()
    from agents.reception import ReceptionAgent
    import asyncio

    agent = ReceptionAgent(db)
    msg = {
        "customer_name": "重复用户",
        "customer_id": "dup_001",
        "title": "相同问题",
        "content": "反复咨询",
    }
    ticket1 = asyncio.run(agent.receive_from_channel("manual", msg))
    ticket2 = asyncio.run(agent.receive_from_channel("manual", msg))
    db.close()

    assert ticket1 is not None
    assert ticket2 is None


def test_channel_message_normalization():
    """Test that channel adapters correctly normalize messages."""
    from channels.taobao import TaobaoAdapter

    adapter = TaobaoAdapter()
    raw = {
        "tid": "123456",
        "buyer": {"nick": "张三", "id": "buyer_001"},
        "title": "退货咨询",
        "content": "我想退货，商品有质量问题",
    }
    msg = adapter.normalize(raw)
    assert msg.channel == "taobao"
    assert msg.customer_name == "张三"
    assert "退货" in msg.title
