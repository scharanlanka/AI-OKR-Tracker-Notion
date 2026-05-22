# AI OKR Tracker MVP (Sprint 1)

Beginner-friendly full-stack vertical slice:

Notion mock OKR data -> PostgreSQL -> FastAPI -> LangGraph agents -> Streamlit UI

## Project Structure

```text
okr-tracker/
├── backend/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── llm.py
│   ├── notion_service.py
│   ├── okr_service.py
│   ├── agents/
│   │   ├── graph.py
│   │   ├── router_agent.py
│   │   ├── risk_agent.py
│   │   ├── deadline_agent.py
│   │   ├── blocker_agent.py
│   │   ├── team_agent.py
│   │   └── general_agent.py
│   └── requirements.txt
├── frontend/
│   ├── app.py
│   └── requirements.txt
├── scripts/
│   └── create_mock_notion_workspace.py
├── .env.example
├── README.md
└── docker-compose.yml
```

## 1) Setup Environment

1. Copy env file:

```bash
cp .env.example .env
```

2. Fill values in `.env`:
- `NOTION_TOKEN`
- `NOTION_OBJECTIVES_DB_ID`
- `NOTION_KEY_RESULTS_DB_ID`
- Optional Azure LLM values:
  - `AZURE_LLM_ENDPOINT`
  - `AZURE_LLM_API_KEY`
  - `AZURE_LLM_DEPLOYMENT_NAME`

LLM is optional. If API key is missing, agents use rule-based summaries.

## 2) Start PostgreSQL

```bash
docker compose up -d db
```

This maps host `5433` -> container `5432`, so default `DATABASE_URL` uses port `5433`.

## 3) Run Backend

```bash
cd backend
uv sync
uv run python init_db.py
uv run uvicorn main:app --reload --port 8001
```

Backend endpoints:
- `GET /health`
- `POST /sync/notion`
- `GET /okrs`
- `GET /okrs/risks`
- `GET /okrs/deadlines`
- `POST /ask`

## 4) Run Frontend

Open a second terminal:

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8001
```

Set `BACKEND_URL` in `.env` if backend is not `http://localhost:8001`.

## 5) Test Flow

1. Click **Sync Notion** in Streamlit.
2. Verify dashboard metrics populate.
3. Open **Risk Report** and **Upcoming Deadlines** tables.
4. Ask assistant questions such as:
   - "What are our top risks?"
   - "Which KRs are due soon?"
   - "Show blocked work"

## Azure LLM Notes

`backend/llm.py` calls `AZURE_LLM_ENDPOINT` directly using OpenAI-compatible payload:

```json
{
  "model": "AZURE_LLM_DEPLOYMENT_NAME",
  "messages": [...]
}
```

Headers include both `api-key` and `Authorization: Bearer ...` for compatibility.
Errors are logged clearly and fallback logic prevents crashes.

## Sprint 1 Scope

Included:
- FastAPI + SQLAlchemy + PostgreSQL
- Notion sync service (insert/update)
- LangGraph router + 5 specialist agents
- Streamlit dashboard + assistant input

Not included (intentionally):
- Auth
- Slack/email integrations
- Vector DB/RAG complexity
- Deployment infra
