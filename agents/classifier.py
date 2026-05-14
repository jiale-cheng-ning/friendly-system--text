from datetime import datetime
from sqlalchemy.orm import Session
from models.ticket import Ticket, TicketStatus
from models.intent import ClassificationResult
from services.intent_service import classify, get_category_by_code


class ClassifierAgent:
    """Intent classification and routing agent."""

    def __init__(self, db: Session):
        self.db = db

    async def classify_ticket(self, ticket: Ticket) -> ClassificationResult:
        ticket.status = TicketStatus.CLASSIFYING.value
        ticket.updated_at = datetime.utcnow()
        self.db.commit()

        result = await classify(ticket.content)
        if not result:
            result = ClassificationResult(
                major_code="C12", major_name="其他",
                sub_category="其他杂项", confidence=0.5,
                route="human", priority="P3", reasoning="分类失败，默认转人工",
            )

        ticket.major_category = f"{result.major_code} {result.major_name}"
        ticket.sub_category = result.sub_category
        ticket.confidence = result.confidence
        ticket.priority = result.priority
        ticket.updated_at = datetime.utcnow()

        if result.route == "human":
            ticket.status = TicketStatus.PENDING_HUMAN.value
        elif result.route == "semi":
            ticket.status = TicketStatus.AUTO_REPLYING.value
        else:
            ticket.status = TicketStatus.AUTO_REPLYING.value

        self.db.commit()
        return result

    async def classify_and_route(self, ticket: Ticket) -> dict:
        result = await self.classify_ticket(ticket)
        return {
            "ticket_id": ticket.id,
            "major": f"{result.major_code} {result.major_name}",
            "sub": result.sub_category,
            "confidence": result.confidence,
            "route": result.route,
            "priority": result.priority,
            "status": ticket.status,
        }
