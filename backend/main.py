import logging
import json
from pathlib import Path
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from agents.graph import OKRGraph
from db import Base, engine, get_db
from models import AgentLog
from notion_service import sync_from_notion
from okr_service import get_all_okrs, get_risks, get_upcoming_deadlines
from schemas import AskRequest, AskResponse, DeadlineItem, ObjectiveOut, RiskItem

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler(),
    ],
    force=True,
)
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
    request_start = perf_counter()
    try:
        result = sync_from_notion(db)
        logger.info("/sync/notion completed in %.3fs", perf_counter() - request_start)
        return {"message": "Notion sync completed", **result}
    except Exception as exc:  # noqa: BLE001
        logger.info("/sync/notion failed in %.3fs", perf_counter() - request_start)
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
    request_start = perf_counter()
    logger.info("/ask request started question=%r", payload.question)
    try:
        route_start = perf_counter()
        route, answer = agent_graph.run(payload.question, db)
        logger.info("/ask graph completed route=%s in %.3fs", route, perf_counter() - route_start)

        persist_start = perf_counter()
        log = AgentLog(question=payload.question, routed_agent=route, response=answer)
        db.add(log)
        db.commit()
        logger.info("/ask response persisted in %.3fs", perf_counter() - persist_start)
        logger.info("/ask request completed in %.3fs", perf_counter() - request_start)

        return AskResponse(agent=route, answer=answer)
    except Exception as exc:  # noqa: BLE001
        logger.info("/ask request failed in %.3fs", perf_counter() - request_start)
        logger.exception("Agent query failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent query failed: {exc}")


@app.post("/ask/stream")
def ask_assistant_stream(payload: AskRequest, db: Session = Depends(get_db)):
    request_start = perf_counter()
    logger.info("/ask/stream request started question=%r", payload.question)
    try:
        route_start = perf_counter()
        route, token_stream = agent_graph.stream(payload.question, db)
        logger.info("/ask/stream route resolved route=%s in %.3fs", route, perf_counter() - route_start)
    except Exception as exc:  # noqa: BLE001
        logger.info("/ask/stream setup failed in %.3fs", perf_counter() - request_start)
        logger.exception("Agent stream setup failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent stream setup failed: {exc}")

    def event_stream():
        stream_start = perf_counter()
        chunks: list[str] = []
        try:
            yield f"data: {json.dumps({'type': 'meta', 'agent': route})}\n\n"
            chunk_count = 0
            for chunk in token_stream:
                chunks.append(chunk)
                chunk_count += 1
                yield f"data: {json.dumps({'type': 'token', 'text': chunk})}\n\n"
            answer = "".join(chunks).strip()
            persist_start = perf_counter()
            log = AgentLog(question=payload.question, routed_agent=route, response=answer)
            db.add(log)
            db.commit()
            logger.info(
                "/ask/stream completed route=%s chunks=%s stream_time=%.3fs persist_time=%.3fs total_time=%.3fs",
                route,
                chunk_count,
                perf_counter() - stream_start,
                perf_counter() - persist_start,
                perf_counter() - request_start,
            )
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent streaming failed: %s", exc)
            db.rollback()
            logger.info("/ask/stream failed after %.3fs", perf_counter() - request_start)
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
