from datetime import date, datetime, timedelta
import json
from typing import Any

from sqlalchemy.orm import Session

from llm import AzureLLMClient
from models import KeyResult, Objective
from notion_service import (
    archive_page_in_notion,
    create_key_result_in_notion,
    create_objective_in_notion,
    update_key_result_in_notion,
    update_objective_in_notion,
)


class WriteAgent:
    """Schema-aware write agent: infer action + fields from NL and execute in Notion."""

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def _default_plan(self) -> dict[str, Any]:
        return {
            "entity": "objective",
            "action": "create",
            "target_filters": {},
            "values": {},
        }

    def _parse_date_iso(self, value: str | None) -> str | None:
        if not value:
            return None
        value = value.strip().lower()
        today = date.today()
        if value == "today":
            return today.isoformat()
        if value == "tomorrow":
            return (today + timedelta(days=1)).isoformat()
        if value == "yesterday":
            return (today - timedelta(days=1)).isoformat()
        if value in {"next week", "in a week"}:
            return (today + timedelta(days=7)).isoformat()
        if value in {"next month", "in a month"}:
            return (today + timedelta(days=30)).isoformat()
        for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d %Y"):
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return value if len(value) == 10 and value[4] == "-" and value[7] == "-" else None

    def _infer_write_plan(self, question: str) -> dict[str, Any]:
        plan = self._default_plan()
        if not self.llm_client.is_enabled:
            return plan

        out = self.llm_client.chat(
            system_prompt=(
                "You convert a natural-language OKR WRITE request into strict JSON.\n"
                "Return JSON only.\n"
                f"Today is {date.today().isoformat()}.\n"
                "Resolve relative date words to YYYY-MM-DD in values.deadline.\n"
                "{"
                "\"entity\":\"objective|key_result\","
                "\"action\":\"create|update|delete\","
                "\"target_filters\":{"
                "\"title\":\"string\","
                "\"objective_title\":\"string\","
                "\"owner\":\"string\","
                "\"team\":\"string\""
                "},"
                "\"values\":{"
                "\"title\":\"string\","
                "\"objective_title\":\"string\","
                "\"owner\":\"string\","
                "\"team\":\"string\","
                "\"quarter\":\"string\","
                "\"status\":\"string\","
                "\"risk\":\"string\","
                "\"progress\":0..1,"
                "\"deadline\":\"YYYY-MM-DD\","
                "\"blocker_notes\":\"string\""
                "}"
                "}\n"
                "For create, populate values with fields to set.\n"
                "For update/delete, use target_filters to identify row(s), values for updates.\n"
                "Do not include extra keys."
            ),
            prompt=f"Request: {question}",
        )
        try:
            candidate = json.loads((out or "").strip())
            if isinstance(candidate, dict):
                plan.update(candidate)
        except json.JSONDecodeError:
            return plan

        if plan.get("entity") not in {"objective", "key_result"}:
            plan["entity"] = "objective"
        if plan.get("action") not in {"create", "update", "delete"}:
            plan["action"] = "create"
        if not isinstance(plan.get("target_filters"), dict):
            plan["target_filters"] = {}
        if not isinstance(plan.get("values"), dict):
            plan["values"] = {}
        return plan

    def _match_objectives(self, db: Session, filters: dict[str, Any]) -> list[Objective]:
        q = db.query(Objective)
        if filters.get("title"):
            q = q.filter(Objective.title.ilike(f"%{filters['title']}%"))
        if filters.get("owner"):
            q = q.filter(Objective.owner.ilike(f"%{filters['owner']}%"))
        if filters.get("team"):
            q = q.filter(Objective.team.ilike(f"%{filters['team']}%"))
        return q.order_by(Objective.updated_at.desc()).all()

    def _match_key_results(self, db: Session, filters: dict[str, Any]) -> list[tuple[KeyResult, Objective]]:
        q = db.query(KeyResult, Objective).join(Objective, KeyResult.objective_id == Objective.id)
        if filters.get("title"):
            q = q.filter(KeyResult.title.ilike(f"%{filters['title']}%"))
        if filters.get("objective_title"):
            q = q.filter(Objective.title.ilike(f"%{filters['objective_title']}%"))
        if filters.get("owner"):
            q = q.filter(KeyResult.owner.ilike(f"%{filters['owner']}%"))
        if filters.get("team"):
            q = q.filter(KeyResult.team.ilike(f"%{filters['team']}%"))
        return q.order_by(KeyResult.updated_at.desc()).all()

    def _create_objective(self, values: dict[str, Any]) -> str:
        title = values.get("title")
        if not title:
            return "Missing required field: objective title."
        created = create_objective_in_notion(
            title=title,
            owner=values.get("owner"),
            team=values.get("team"),
            quarter=values.get("quarter"),
            status=values.get("status"),
            progress=values.get("progress"),
        )
        return f"Created objective '{title}'. Notion page id: {created.get('id', 'unknown')}."

    def _create_key_result(self, values: dict[str, Any], db: Session) -> str:
        title = values.get("title")
        if not title:
            return "Missing required field: key result title."
        objective_title = (values.get("objective_title") or "").strip()
        if not objective_title:
            return "Missing required field: objective for this key result."

        matches = self._match_objectives(db=db, filters={"title": objective_title})
        if not matches:
            return f"No matching objective found for title '{objective_title}'."
        if len(matches) > 1:
            return f"Multiple objectives matched '{objective_title}'. Please provide a more specific objective title."
        objective = matches[0]

        deadline = self._parse_date_iso(values.get("deadline"))
        created = create_key_result_in_notion(
            title=title,
            objective_notion_id=objective.notion_id,
            owner=values.get("owner"),
            team=values.get("team"),
            risk=values.get("risk"),
            status=values.get("status"),
            deadline=deadline,
            progress=values.get("progress"),
        )
        return (
            f"Created key result '{title}' under objective '{objective.title}'. "
            f"Notion page id: {created.get('id', 'unknown')}."
        )

    def run(self, question: str, db: Session) -> str:
        plan = self._infer_write_plan(question)
        entity = plan["entity"]
        action = plan["action"]
        filters = plan.get("target_filters", {})
        values = plan.get("values", {})

        if action == "create":
            if entity == "objective":
                return self._create_objective(values)
            return self._create_key_result(values, db)

        if entity == "objective":
            matches = self._match_objectives(db, filters)
            if not matches:
                return "No matching objective found for this write request."
            target = matches[0]
            if action == "delete":
                archive_page_in_notion(target.notion_id)
                return f"Deleted objective '{target.title}' (archived in Notion)."
            updated = update_objective_in_notion(
                notion_id=target.notion_id,
                title=values.get("title"),
                owner=values.get("owner"),
                team=values.get("team"),
                quarter=values.get("quarter"),
                status=values.get("status"),
                progress=values.get("progress"),
            )
            return f"Updated objective '{target.title}'. Notion page id: {updated.get('id', 'unknown')}."

        matches_kr = self._match_key_results(db, filters)
        if not matches_kr:
            return "No matching key result found for this write request."
        kr, obj = matches_kr[0]
        if action == "delete":
            archive_page_in_notion(kr.notion_id)
            return f"Deleted key result '{kr.title}' under '{obj.title}' (archived in Notion)."

        updated = update_key_result_in_notion(
            notion_id=kr.notion_id,
            title=values.get("title"),
            objective_notion_id=self._resolve_objective_notion_id(values.get("objective_title"), db, obj.notion_id),
            owner=values.get("owner"),
            team=values.get("team"),
            risk=values.get("risk"),
            status=values.get("status"),
            deadline=self._parse_date_iso(values.get("deadline")),
            progress=values.get("progress"),
            blocker_notes=values.get("blocker_notes"),
        )
        return (
            f"Updated key result '{kr.title}' under '{obj.title}'. "
            f"Notion page id: {updated.get('id', 'unknown')}."
        )

    def _resolve_objective_notion_id(
        self, objective_title: str | None, db: Session, default_notion_id: str
    ) -> str:
        if not objective_title:
            return default_notion_id
        matches = self._match_objectives(db, {"title": objective_title.strip()})
        if len(matches) == 1:
            return matches[0].notion_id
        return default_notion_id
