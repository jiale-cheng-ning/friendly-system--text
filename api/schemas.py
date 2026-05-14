from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TicketCreateRequest(BaseModel):
    channel: str = "manual"
    customer_name: str = "未知用户"
    customer_id: str = "anonymous"
    title: str
    content: str
    raw_data: Optional[dict] = None


class TicketReplyRequest(BaseModel):
    content: str


class TicketResponse(BaseModel):
    id: int
    external_id: Optional[str]
    channel: str
    customer_name: str
    customer_id: str
    title: str
    content: str
    status: str
    priority: str
    major_category: Optional[str]
    sub_category: Optional[str]
    confidence: float
    auto_reply_rounds: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketDetailResponse(TicketResponse):
    messages: list["MessageResponse"] = []
    handoff: Optional["HandoffResponse"] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class HandoffResponse(BaseModel):
    id: int
    summary: str
    emotion_analysis: Optional[str]
    suggested_action: Optional[str]
    estimated_minutes: int
    matched_skills: Optional[list]
    created_at: datetime

    class Config:
        from_attributes = True


class ClassificationResponse(BaseModel):
    ticket_id: int
    major: str
    sub: str
    confidence: float
    route: str
    priority: str
    status: str


class AutoReplyResponse(BaseModel):
    ticket_id: int
    reply: str
    closed: bool
    round: int
    usage: Optional[dict] = None


class HandoffPrepareResponse(BaseModel):
    ticket_id: int
    summary: str
    emotion: str
    suggested_actions: str
    estimated_minutes: int
    matched_skills: list


class DashboardResponse(BaseModel):
    total_today: int
    resolved_today: int
    pending_human: int
    auto_reply_rate: float
    avg_wait_minutes: float
    by_channel: dict
    by_category: dict
    by_priority: dict
