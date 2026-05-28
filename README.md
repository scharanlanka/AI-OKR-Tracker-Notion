# OKR Tracker (Notion + FastAPI + Next.js + Agentic Assistant)

OKR Tracker is a full-stack app that syncs OKR data from Notion into PostgreSQL, shows it in a Next.js dashboard, and supports natural-language read/write operations through routed agents.

Current architecture:
- `router_agent`: classifies intent -> `read_agent` or `write_agent`
- `read_agent`: schema-aware query planning from natural language
- `write_agent`: schema-aware write planning (`create|update|delete`) to Notion
- Streaming assistant responses over `POST /ask/stream` (SSE-style frames)

## Tech Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, LangGraph
- Frontend: Next.js (App Router), React, Tailwind CSS
- Data source: Notion databases (Objectives + Key Results)
- LLM: Azure OpenAI-compatible endpoint (optional but recommended)

## Project Structure

```text
OKR-Tracker/
├── backend/
│   ├── agents/
│   │   ├── graph.py
│   │   ├── router_agent.py
│   │   ├── read_agent.py
│   │   └── write_agent.py
│   ├── main.py
│   ├── llm.py
│   ├── notion_service.py
│   ├── models.py
│   ├── schemas.py
│   ├── db.py
│   ├── init_db.py
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Environment Variables

Copy and edit:

```bash
cp .env.example .env
```

Required for Notion sync/write:
- `NOTION_TOKEN`
- `NOTION_OBJECTIVES_DB_ID`
- `NOTION_KEY_RESULTS_DB_ID`

Required for DB:
- `DATABASE_URL` (defaults are set for docker-compose in this repo)

Optional but required for LLM routing/planning/streaming:
- `AZURE_LLM_ENDPOINT`
- `AZURE_LLM_API_KEY`
- `AZURE_LLM_DEPLOYMENT_NAME`

Frontend:

```bash
cp frontend/.env.local.example frontend/.env.local
```

- `NEXT_PUBLIC_BACKEND_URL` (example: `http://localhost:8001`)

## Run with Docker DB + Local App

1. Start PostgreSQL:

```bash
docker compose up -d db
```

2. Start backend:

```bash
cd backend
uv sync
uv run python init_db.py
uv run uvicorn main:app --reload --port 8001
```

3. Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:8501`

## Backend API

- `GET /health`
- `POST /sync/notion`
- `GET /okrs`
- `GET /okrs/risks`
- `GET /okrs/deadlines`
- `POST /ask` (non-stream response)
- `POST /ask/stream` (streaming response)

### `/ask` request

```json
{
  "question": "Show upcoming deadlines with progress"
}
```

### `/ask/stream` protocol

`POST /ask/stream` returns `text/event-stream` frames like:

```text
data: {"type":"meta","agent":"read_agent"}

data: {"type":"token","text":"Here "}

data: {"type":"token","text":"are "}

data: {"type":"done"}
```

Possible frame types:
- `meta`: routed agent
- `token`: streamed text chunk
- `done`: stream complete
- `error`: stream failed

## Agent Behavior (Current)

### Router Agent
- Prompt-based intent routing.
- Returns `read_agent` or `write_agent`.

### Read Agent
- Converts NL query into structured plan:
  - entity (`objective|key_result|both`)
  - filters (owner/team/status/risk/progress/date ranges/etc.)
  - sort + limit
- Date-aware defaults for relative queries (`upcoming`, `overdue`, etc.) using current date.
- Special handling for “team with most missed deadlines”.

### Write Agent
- Converts NL request into structured write plan:
  - action (`create|update|delete`)
  - entity (`objective|key_result`)
  - target filters + values
- Executes against Notion pages (create/update/archive).
- Uses SQL data to resolve target records for update/delete.

## Notion Sync Model

- `sync_from_notion` pulls both Notion DBs into local PostgreSQL.
- Local DB is used for reads and for locating records during write updates/deletes.
- Notion remains source of truth for write operations.

## Notes

- Streaming depends on a valid Azure endpoint that supports chat completions with `stream=true`.
- If LLM is unavailable, behavior falls back to deterministic/minimal responses where implemented.
