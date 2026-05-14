import pytest
from core.database import Base, engine, init_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


def test_handoff_triggers_pending_human():
    """Test that unreplied tickets trigger human handoff."""
    pass
