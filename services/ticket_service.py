from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.ticket import Ticket, TicketMessage, HandoffRecord, TicketStatus


class TicketService:
    def __init__(self, db: Session):
        self.db = db

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        return self.db.query(Ticket).filter(Ticket.id == ticket_id).first()

    def list_tickets(
        self, status: str = None, channel: str = None, category: str = None,
        limit: int = 50, offset: int = 0,
    ) -> list[Ticket]:
        q = self.db.query(Ticket)
        if status:
            q = q.filter(Ticket.status == status)
        if channel:
            q = q.filter(Ticket.channel == channel)
        if category:
            q = q.filter(Ticket.major_category.like(f"%{category}%"))
        return q.order_by(Ticket.created_at.desc()).offset(offset).limit(limit).all()

    def get_messages(self, ticket_id: int) -> list[TicketMessage]:
        return self.db.query(TicketMessage).filter(
            TicketMessage.ticket_id == ticket_id
        ).order_by(TicketMessage.created_at).all()

    def get_handoff(self, ticket_id: int) -> HandoffRecord | None:
        return self.db.query(HandoffRecord).filter(
            HandoffRecord.ticket_id == ticket_id
        ).first()

    def get_dashboard(self) -> dict:
        today_start = datetime.combine(date.today(), datetime.min.time())
        q = self.db.query(Ticket)
        total_today = q.filter(Ticket.created_at >= today_start).count()
        resolved_today = q.filter(
            Ticket.created_at >= today_start,
            Ticket.status == TicketStatus.RESOLVED.value,
        ).count()
        pending_human = q.filter(
            Ticket.status.in_([
                TicketStatus.PENDING_HUMAN.value,
                TicketStatus.HUMAN_PROCESSING.value,
            ])
        ).count()

        total = total_today or 1
        resolved = resolved_today
        auto_reply_rate = round(resolved / total * 100, 1)

        by_channel = {}
        for ch in ["taobao", "jd", "douyin", "manual"]:
            cnt = q.filter(
                Ticket.created_at >= today_start,
                Ticket.channel == ch,
            ).count()
            by_channel[ch] = cnt

        by_category = {}
        all_today = q.filter(Ticket.created_at >= today_start).all()
        for t in all_today:
            mc = t.major_category or "未分类"
            by_category[mc] = by_category.get(mc, 0) + 1

        by_priority = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for t in all_today:
            if t.priority in by_priority:
                by_priority[t.priority] += 1

        return {
            "total_today": total_today,
            "resolved_today": resolved_today,
            "pending_human": pending_human,
            "auto_reply_rate": auto_reply_rate,
            "avg_wait_minutes": 15.0,
            "by_channel": by_channel,
            "by_category": by_category,
            "by_priority": by_priority,
        }
