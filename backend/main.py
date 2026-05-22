import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from agents.graph import OKRGraph
from db import Base, engine, get_db
from models import AgentLog
from notion_service import sync_from_notion
from okr_service import get_all_okrs, get_risks, get_upcoming_deadlines
from schemas import AskRequest, AskResponse, DeadlineItem, ObjectiveOut, RiskItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ROOT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ROOT_ENV_PATH, override=True)

app = FastAPI(title="OKR Tracker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
agent_graph = OKRGraph()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sync/notion")
def sync_notion(db: Session = Depends(get_db)):
    try:
        result = sync_from_notion(db)
        return {"message": "Notion sync completed", **result}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Notion sync failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Notion sync failed: {exc}")


@app.get("/okrs", response_model=list[ObjectiveOut])
def list_okrs(db: Session = Depends(get_db)):
    return get_all_okrs(db)


@app.get("/okrs/risks", response_model=list[RiskItem])
def list_risks(db: Session = Depends(get_db)):
    return get_risks(db)


@app.get("/okrs/deadlines", response_model=list[DeadlineItem])
def list_deadlines(db: Session = Depends(get_db)):
    return get_upcoming_deadlines(db)


@app.post("/ask", response_model=AskResponse)
def ask_assistant(payload: AskRequest, db: Session = Depends(get_db)):
    try:
        route, answer = agent_graph.run(payload.question, db)

        log = AgentLog(question=payload.question, routed_agent=route, response=answer)
        db.add(log)
        db.commit()

        return AskResponse(agent=route, answer=answer)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent query failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent query failed: {exc}")
