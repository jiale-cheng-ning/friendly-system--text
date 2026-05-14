import uvicorn
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.middleware import LoggingMiddleware
from core.config import settings
from core.database import init_db
from services.knowledge_service import knowledge_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ecommerce_ticket_agent")

app = FastAPI(
    title="全渠道电商客服工单智能处理 Agent",
    description="多渠道工单接收 → 智能分类路由 → 自动回复/转人工",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(router)

import os

web_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.isdir(web_dir):
    app.mount("/web", StaticFiles(directory=web_dir, html=True), name="web")


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Database initialized")
    logger.info(f"Knowledge base loaded with entries")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")


@app.get("/")
def root():
    return {
        "service": "全渠道电商客服工单智能处理 Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/web",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
