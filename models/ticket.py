from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
import enum


class TicketStatus(str, enum.Enum):
    NEW = "new"
    CLASSIFYING = "classifying"
    AUTO_REPLYING = "auto_replying"
    RESOLVED = "resolved"
    PENDING_HUMAN = "pending_human"
    HUMAN_PROCESSING = "human_processing"
    CLOSED = "closed"


class Priority(str, enum.Enum):
    P0 = "P0"  # 紧急（敏感事件）
    P1 = "P1"  # 高
    P2 = "P2"  # 中
    P3 = "P3"  # 低


class Channel(str, enum.Enum):
    TAOBAO = "taobao"
    JD = "jd"
    DOUYIN = "douyin"
    MANUAL = "manual"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(128), index=True, comment="外部渠道工单ID")
    channel = Column(String(32), default=Channel.MANUAL.value)
    customer_name = Column(String(64))
    customer_id = Column(String(64), index=True)
    title = Column(String(256))
    content = Column(Text)
    status = Column(String(32), default=TicketStatus.NEW.value, index=True)
    priority = Column(String(8), default=Priority.P2.value)
    major_category = Column(String(64), index=True)
    sub_category = Column(String(64))
    confidence = Column(Float, default=0.0)
    auto_reply_rounds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    raw_data = Column(JSON, comment="渠道原始数据")

    messages = relationship("TicketMessage", back_populates="ticket", order_by="TicketMessage.created_at")
    handoff = relationship("HandoffRecord", back_populates="ticket", uselist=False)


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    role = Column(String(16), comment="customer / agent / system")
    content = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="messages")


class HandoffRecord(Base):
    __tablename__ = "handoff_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    summary = Column(Text)
    emotion_analysis = Column(String(128))
    suggested_action = Column(Text)
    estimated_minutes = Column(Integer)
    matched_skills = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="handoff")
