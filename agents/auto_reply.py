from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from models.ticket import Ticket, TicketMessage, TicketStatus
from core.llm import llm_client
from core.memory import memory
from core.config import settings
from services.knowledge_service import knowledge_service


class AutoReplyAgent:
    """Auto-reply agent with chain-of-thought reasoning."""

    def __init__(self, db: Session):
        self.db = db

    async def generate_reply(self, ticket: Ticket) -> dict:
        ticket.status = TicketStatus.AUTO_REPLYING.value
        ticket.auto_reply_rounds += 1
        self.db.commit()

        kn_results = knowledge_service.search(ticket.content, top_k=3)
        kn_formatted = knowledge_service.format_results(kn_results)
        history = memory.get_formatted(ticket.id)

        prompt = self._load_prompt()
        user_msg = (
            prompt
            .replace("{TICKET_ID}", str(ticket.id))
            .replace("{CHANNEL}", ticket.channel)
            .replace("{MAJOR_CATEGORY}", ticket.major_category or "未分类")
            .replace("{SUB_CATEGORY}", ticket.sub_category or "")
            .replace("{CUSTOMER_NAME}", ticket.customer_name)
            .replace("{HISTORY}", history)
            .replace("{KNOWLEDGE_RESULTS}", kn_formatted)
        )

        resp = await llm_client.chat(
            system="你是一个专业、友好、高效的电商客服代表。",
            user=user_msg,
            temperature=0.5,
            max_tokens=2048,
        )

        closed = self._check_closed(resp.content)

        self.db.add(TicketMessage(
            ticket_id=ticket.id,
            role="agent",
            content=resp.content,
            metadata={"auto_reply_round": ticket.auto_reply_rounds, "closed": closed},
        ))
        self.db.commit()
        memory.add(ticket.id, "agent", resp.content)

        if closed:
            ticket.status = TicketStatus.RESOLVED.value
            ticket.resolved_at = datetime.utcnow()
            self.db.commit()

        if ticket.auto_reply_rounds >= settings.AUTO_REPLY_MAX_ROUNDS and not closed:
            ticket.status = TicketStatus.PENDING_HUMAN.value
            self.db.commit()

        return {
            "ticket_id": ticket.id,
            "reply": resp.content,
            "closed": closed,
            "round": ticket.auto_reply_rounds,
            "usage": resp.usage,
        }

    def _check_closed(self, reply: str) -> bool:
        closed_markers = [
            "问题是否已解决: 是", "是否闭环: 是",
            "已解决", "已处理完毕", "闭环",
        ]
        return any(m in reply for m in closed_markers)

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "auto_reply.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
