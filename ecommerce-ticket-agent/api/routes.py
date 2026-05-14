from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from agents import ReceptionAgent, ClassifierAgent, AutoReplyAgent, HandoffAgent
from services.ticket_service import TicketService
from services.knowledge_service import knowledge_service
from api.schemas import (
    TicketCreateRequest, TicketReplyRequest, TicketResponse,
    TicketDetailResponse, ClassificationResponse, AutoReplyResponse,
    HandoffPrepareResponse, DashboardResponse,
)

router = APIRouter(prefix="/api")


@router.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(req: TicketCreateRequest, db: Session = Depends(get_db)):
    agent = ReceptionAgent(db)
    ticket = await agent.receive_from_channel(req.channel, req.raw_data or {
        "customer_name": req.customer_name,
        "customer_id": req.customer_id,
        "title": req.title,
        "content": req.content,
    })
    if not ticket:
        raise HTTPException(409, "Duplicate ticket")
    classifier = ClassifierAgent(db)
    await classifier.classify_and_route(ticket)
    db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=list[TicketResponse])
async def list_tickets(
    status: str = None, channel: str = None, category: str = None,
    limit: int = 50, offset: int = 0, db: Session = Depends(get_db),
):
    svc = TicketService(db)
    return svc.list_tickets(status, channel, category, limit, offset)


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    svc = TicketService(db)
    ticket = svc.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    result = TicketDetailResponse.model_validate(ticket)
    result.messages = svc.get_messages(ticket_id)
    handoff = svc.get_handoff(ticket_id)
    if handoff:
        result.handoff = handoff
    return result


@router.post("/tickets/{ticket_id}/classify", response_model=ClassificationResponse)
async def classify_ticket(ticket_id: int, db: Session = Depends(get_db)):
    svc = TicketService(db)
    ticket = svc.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    agent = ClassifierAgent(db)
    return await agent.classify_and_route(ticket)


@router.post("/tickets/{ticket_id}/reply", response_model=AutoReplyResponse)
async def auto_reply(ticket_id: int, req: TicketReplyRequest = None, db: Session = Depends(get_db)):
    svc = TicketService(db)
    ticket = svc.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    if req and req.content:
        recv = ReceptionAgent(db)
        await recv.add_customer_message(ticket_id, req.content)
    agent = AutoReplyAgent(db)
    return await agent.generate_reply(ticket)


@router.post("/tickets/{ticket_id}/handoff", response_model=HandoffPrepareResponse)
async def handoff_ticket(ticket_id: int, db: Session = Depends(get_db)):
    svc = TicketService(db)
    ticket = svc.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    agent = HandoffAgent(db)
    return await agent.prepare_handoff(ticket)


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(db: Session = Depends(get_db)):
    svc = TicketService(db)
    return svc.get_dashboard()


@router.get("/knowledge/search")
async def search_knowledge(q: str, top_k: int = 5):
    results = knowledge_service.search(q, top_k)
    return {"query": q, "results": results}
