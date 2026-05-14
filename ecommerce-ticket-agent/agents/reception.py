import hashlib
import time
from datetime import datetime
from sqlalchemy.orm import Session
from models.ticket import Ticket, TicketMessage, TicketStatus, Channel
from channels import get_adapter, ChannelMessage
from core.memory import memory


class ReceptionAgent:
    """Unified ticket reception from all channels."""

    def __init__(self, db: Session):
        self.db = db

    async def receive_from_channel(self, channel: str, raw_message: dict) -> Ticket | None:
        adapter = get_adapter(channel)
        if not adapter:
            msg = ChannelMessage(
                external_id=f"manual_{int(time.time())}",
                customer_name=raw_message.get("customer_name", "未知用户"),
                customer_id=raw_message.get("customer_id", "anonymous"),
                title=raw_message.get("title", "手动工单"),
                content=raw_message.get("content", ""),
                channel="manual",
                raw_data=raw_message,
            )
        else:
            msg = adapter.normalize(raw_message)

        if self._is_duplicate(msg):
            return None

        ticket = Ticket(
            external_id=msg.external_id,
            channel=msg.channel,
            customer_name=msg.customer_name,
            customer_id=msg.customer_id,
            title=msg.title,
            content=msg.content,
            status=TicketStatus.NEW.value,
            raw_data=msg.raw_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        self.db.add(TicketMessage(
            ticket_id=ticket.id,
            role="customer",
            content=msg.content,
        ))
        self.db.commit()

        memory.add(ticket.id, "customer", msg.content)
        return ticket

    async def receive_batch(self, channel: str) -> list[Ticket]:
        adapter = get_adapter(channel)
        if not adapter:
            return []
        messages = await adapter.fetch_tickets()
        tickets = []
        for msg in messages:
            ticket = await self.receive_from_channel(channel, msg.raw_data)
            if ticket:
                tickets.append(ticket)
        return tickets

    async def add_customer_message(self, ticket_id: int, content: str):
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return
        self.db.add(TicketMessage(
            ticket_id=ticket_id,
            role="customer",
            content=content,
        ))
        ticket.updated_at = datetime.utcnow()
        self.db.commit()
        memory.add(ticket_id, "customer", content)

    def _is_duplicate(self, msg: ChannelMessage) -> bool:
        recent = self.db.query(Ticket).filter(
            Ticket.customer_id == msg.customer_id,
            Ticket.title == msg.title,
        ).order_by(Ticket.created_at.desc()).first()
        if recent and (datetime.utcnow() - recent.created_at).seconds < 3600:
            return True
        return False
