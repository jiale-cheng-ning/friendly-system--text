from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from models.ticket import Ticket, TicketMessage, HandoffRecord, TicketStatus
from core.llm import llm_client
from core.memory import memory


class HandoffAgent:
    """Context preparation for human agent handoff."""

    def __init__(self, db: Session):
        self.db = db

    async def prepare_handoff(self, ticket: Ticket) -> dict:
        ticket.status = TicketStatus.PENDING_HUMAN.value
        self.db.commit()

        messages = self.db.query(TicketMessage).filter(
            TicketMessage.ticket_id == ticket.id
        ).order_by(TicketMessage.created_at).all()

        conversation = "\n".join(
            f"{'客户' if m.role == 'customer' else '客服' if m.role == 'agent' else '系统'}: {m.content}"
            for m in messages
        )

        auto_attempts = "\n".join(
            m.content[:200] for m in messages if m.role == "agent"
        ) or "无自动回复记录"

        prompt = self._load_prompt()
        user_msg = (
            prompt
            .replace("{TICKET_ID}", str(ticket.id))
            .replace("{CHANNEL}", ticket.channel)
            .replace("{MAJOR_CATEGORY}", ticket.major_category or "未分类")
            .replace("{SUB_CATEGORY}", ticket.sub_category or "")
            .replace("{PRIORITY}", ticket.priority or "P2")
            .replace("{CUSTOMER_NAME}", ticket.customer_name)
            .replace("{CONVERSATION_HISTORY}", conversation)
            .replace("{AUTO_REPLY_ATTEMPTS}", auto_attempts)
        )

        result = await llm_client.chat_with_json_output(
            system="你是一个精确的客服工单分析专家。严格输出JSON格式。",
            user=user_msg,
            temperature=0.3,
        )

        record = HandoffRecord(
            ticket_id=ticket.id,
            summary=result.get("summary", ""),
            emotion_analysis=result.get("emotion", ""),
            suggested_action=result.get("suggested_actions", ""),
            estimated_minutes=result.get("estimated_minutes", 15),
            matched_skills=result.get("matched_skills", []),
        )
        self.db.add(record)

        self.db.add(TicketMessage(
            ticket_id=ticket.id,
            role="system",
            content=f"已转人工 | 情绪: {record.emotion_analysis} | 建议: {record.suggested_action}",
            metadata={"handoff": True},
        ))

        self.db.commit()
        memory.clear(ticket.id)

        return {
            "ticket_id": ticket.id,
            "summary": record.summary,
            "emotion": record.emotion_analysis,
            "suggested_actions": record.suggested_action,
            "estimated_minutes": record.estimated_minutes,
            "matched_skills": record.matched_skills,
        }

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "handoff.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
