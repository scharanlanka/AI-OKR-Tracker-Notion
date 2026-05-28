from datetime import date, datetime
import json
import re
from typing import Any

from sqlalchemy.orm import Session

from llm import AzureLLMClient
from models import KeyResult, Objective


class ReadAgent:
    """Schema-aware read agent that infers structured filters from NL queries."""

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def _normalize(self, text: str | None) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip().lower()

    def _parse_date(self, text: str | None) -> date | None:
        if not text:
            return None
        t = text.strip()
        for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d %Y"):
            try:
                return datetime.strptime(t, fmt).date()
            except ValueError:
                continue
        return None

    def _to_objective_rows(self, objectives: list[Objective]) -> list[dict[str, Any]]:
        return [
            {
                "title": o.title,
                "owner": o.owner,
                "team": o.team,
                "quarter": o.quarter,
                "status": o.status,
                "progress": o.progress,
                "target_date": str(o.target_date) if o.target_date else None,
            }
            for o in objectives
        ]

    def _to_kr_rows(self, kr_pairs: list[tuple[KeyResult, Objective]]) -> list[dict[str, Any]]:
        return [
            {
                "objective_title": obj.title,
                "title": kr.title,
                "owner": kr.owner,
                "team": kr.team,
                "risk": kr.risk,
                "status": kr.status,
                "progress": kr.progress,
                "deadline": str(kr.deadline) if kr.deadline else None,
                "last_update": str(kr.last_update) if kr.last_update else None,
                "is_blocked": kr.is_blocked,
                "blocker_notes": kr.blocker_notes,
            }
            for kr, obj in kr_pairs
        ]

    def _default_plan(self, question: str) -> dict[str, Any]:
        q = self._normalize(question)
        entity = "both"
        if "objective" in q:
            entity = "objective"
        elif "key result" in q or re.search(r"\bkr\b", q):
            entity = "key_result"

        return {
            "entity": entity,
            "intent": "list",
            "filters": {},
            "sort_by": None,
            "sort_order": "asc",
            "limit": 50,
        }

    def _today_iso(self) -> str:
        return date.today().isoformat()

    def _infer_query_plan(self, question: str) -> dict[str, Any]:
        plan = self._default_plan(question)
        if not self.llm_client.is_enabled:
            return plan

        schema_hint = {
            "objective_fields": ["title", "owner", "team", "quarter", "status", "progress", "target_date"],
            "key_result_fields": [
                "title",
                "objective_title",
                "owner",
                "team",
                "risk",
                "status",
                "progress",
                "deadline",
                "last_update",
                "is_blocked",
                "blocker_notes",
            ],
        }

        out = self.llm_client.chat(
            system_prompt=(
                "You convert a natural-language OKR read question into a strict JSON query plan.\n"
                "Return JSON only. No markdown.\n"
                f"Today is {self._today_iso()}.\n"
                "Resolve relative dates (today/tomorrow/next week/this quarter/upcoming/past) against this date.\n"
                "Schema:\n"
                "{"
                "\"entity\":\"objective|key_result|both\","
                "\"intent\":\"list|count|summary\","
                "\"filters\":{"
                "\"title\":\"string\","
                "\"objective_title\":\"string\","
                "\"owner\":\"string\","
                "\"team\":\"string\","
                "\"quarter\":\"string\","
                "\"status\":\"string\","
                "\"risk\":\"string\","
                "\"blocker_notes\":\"string\","
                "\"is_blocked\":true|false,"
                "\"progress_min\":0..1,"
                "\"progress_max\":0..1,"
                "\"deadline_before\":\"YYYY-MM-DD\","
                "\"deadline_after\":\"YYYY-MM-DD\","
                "\"target_date_before\":\"YYYY-MM-DD\","
                "\"target_date_after\":\"YYYY-MM-DD\""
                "},"
                "\"sort_by\":\"field_name_or_null\","
                "\"sort_order\":\"asc|desc\","
                "\"limit\":1..100"
                "}\n"
                "Use only fields present in schema. Omit unknown filters."
            ),
            prompt=f"Question: {question}\nAvailable schema: {json.dumps(schema_hint)}",
        )

        try:
            candidate = json.loads((out or "").strip())
            if isinstance(candidate, dict):
                plan.update(candidate)
        except json.JSONDecodeError:
            return plan

        if plan.get("entity") not in {"objective", "key_result", "both"}:
            plan["entity"] = "both"
        if plan.get("intent") not in {"list", "count", "summary"}:
            plan["intent"] = "list"
        if not isinstance(plan.get("filters"), dict):
            plan["filters"] = {}
        if plan.get("sort_order") not in {"asc", "desc"}:
            plan["sort_order"] = "asc"
        limit = plan.get("limit")
        if not isinstance(limit, int):
            plan["limit"] = 50
        else:
            plan["limit"] = max(1, min(100, limit))
        return self._apply_relative_defaults(question, plan)

    def _apply_relative_defaults(self, question: str, plan: dict[str, Any]) -> dict[str, Any]:
        q = self._normalize(question)
        filters = plan.get("filters", {})
        if not isinstance(filters, dict):
            filters = {}

        has_deadline_filter = any(k in filters for k in ["deadline_before", "deadline_after"])
        if not has_deadline_filter and plan.get("entity") in {"key_result", "both"}:
            today = self._today_iso()
            if any(x in q for x in ["upcoming", "next", "future"]):
                filters["deadline_after"] = today
                plan["sort_by"] = plan.get("sort_by") or "deadline"
                plan["sort_order"] = plan.get("sort_order") or "asc"
            if any(x in q for x in ["past due", "overdue", "missed", "late", "past deadline", "past deadlines"]):
                filters["deadline_before"] = today
                plan["sort_by"] = plan.get("sort_by") or "deadline"
                plan["sort_order"] = plan.get("sort_order") or "desc"
        plan["filters"] = filters
        return plan

    def _is_team_most_missed_query(self, question: str) -> bool:
        q = self._normalize(question)
        return (
            "team" in q
            and ("most" in q or "max" in q)
            and any(x in q for x in ["missed", "past due", "overdue", "late", "past deadline", "past deadlines"])
        )

    def _contains(self, row_value: Any, query_value: str) -> bool:
        return self._normalize(str(row_value)) and self._normalize(query_value) in self._normalize(str(row_value))

    def _filter_rows(self, rows: list[dict[str, Any]], filters: dict[str, Any], is_kr: bool) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in rows:
            ok = True
            for field in [
                "title",
                "objective_title",
                "owner",
                "team",
                "quarter",
                "status",
                "risk",
                "blocker_notes",
            ]:
                val = filters.get(field)
                if val and not self._contains(row.get(field), str(val)):
                    ok = False
                    break

            if not ok:
                continue

            if "is_blocked" in filters and is_kr:
                if bool(row.get("is_blocked")) != bool(filters["is_blocked"]):
                    continue

            pmin = filters.get("progress_min")
            pmax = filters.get("progress_max")
            progress = float(row.get("progress") or 0.0)
            if pmin is not None and progress < float(pmin):
                continue
            if pmax is not None and progress > float(pmax):
                continue

            if is_kr:
                d = self._parse_date(row.get("deadline"))
                d_before = self._parse_date(filters.get("deadline_before"))
                d_after = self._parse_date(filters.get("deadline_after"))
                if d_before and (d is None or d >= d_before):
                    continue
                if d_after and (d is None or d <= d_after):
                    continue
            else:
                t = self._parse_date(row.get("target_date"))
                t_before = self._parse_date(filters.get("target_date_before"))
                t_after = self._parse_date(filters.get("target_date_after"))
                if t_before and (t is None or t >= t_before):
                    continue
                if t_after and (t is None or t <= t_after):
                    continue

            out.append(row)
        return out

    def _sort_rows(self, rows: list[dict[str, Any]], sort_by: str | None, sort_order: str) -> list[dict[str, Any]]:
        if not sort_by:
            return rows
        reverse = sort_order == "desc"
        return sorted(rows, key=lambda r: (r.get(sort_by) is None, str(r.get(sort_by))), reverse=reverse)

    def run(self, question: str, db: Session) -> str:
        kr_pairs = (
            db.query(KeyResult, Objective)
            .join(Objective, KeyResult.objective_id == Objective.id)
            .order_by(KeyResult.updated_at.desc())
            .all()
        )
        objectives = db.query(Objective).order_by(Objective.updated_at.desc()).all()

        objective_rows = self._to_objective_rows(objectives)
        kr_rows = self._to_kr_rows(kr_pairs)

        if self._is_team_most_missed_query(question):
            today = self._today_iso()
            counts: dict[str, int] = {}
            for row in kr_rows:
                d = row.get("deadline")
                if d and d < today:
                    team = row.get("team") or "Unassigned"
                    counts[team] = counts.get(team, 0) + 1
            if not counts:
                return f"No team has missed deadlines before {today}."
            ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            top_team, top_count = ranked[0]
            ties = [t for t, c in ranked if c == top_count]
            if len(ties) > 1:
                return f"Tie for most missed deadlines before {today}: {', '.join(ties)} ({top_count} each)."
            return f"Team with most missed deadlines before {today}: {top_team} ({top_count})."

        plan = self._infer_query_plan(question)

        entity = plan.get("entity", "both")
        filters = plan.get("filters", {})
        sort_by = plan.get("sort_by")
        sort_order = plan.get("sort_order", "asc")
        limit = plan.get("limit", 50)

        filtered_objectives: list[dict[str, Any]] = []
        filtered_key_results: list[dict[str, Any]] = []

        if entity in {"objective", "both"}:
            filtered_objectives = self._sort_rows(
                self._filter_rows(objective_rows, filters, is_kr=False), sort_by, sort_order
            )[:limit]
        if entity in {"key_result", "both"}:
            filtered_key_results = self._sort_rows(
                self._filter_rows(kr_rows, filters, is_kr=True), sort_by, sort_order
            )[:limit]

        facts = {
            "query_plan": plan,
            "objectives": filtered_objectives,
            "key_results": filtered_key_results,
        }

        if not filtered_objectives and not filtered_key_results:
            facts["objectives"] = objective_rows[: min(30, len(objective_rows))]
            facts["key_results"] = kr_rows[: min(50, len(kr_rows))]
            facts["fallback_mode"] = "broad_context"

        if not self.llm_client.is_enabled:
            if filtered_key_results:
                return "\n".join(
                    [
                        f"- {r['title']} ({r['objective_title']}) owner={r.get('owner') or 'N/A'} "
                        f"team={r.get('team') or 'N/A'} status={r.get('status') or 'N/A'} "
                        f"progress={int((r.get('progress') or 0.0) * 100)}%"
                        for r in filtered_key_results[:12]
                    ]
                )
            if filtered_objectives:
                return "\n".join(
                    [
                        f"- {r['title']} owner={r.get('owner') or 'N/A'} "
                        f"team={r.get('team') or 'N/A'} status={r.get('status') or 'N/A'} "
                        f"progress={int((r.get('progress') or 0.0) * 100)}%"
                        for r in filtered_objectives[:12]
                    ]
                )
            return "No matches found."

        response = self.llm_client.chat(
            system_prompt=self._read_system_prompt(),
            prompt=self._read_user_prompt(question, facts),
        )
        return response or "I could not generate a response from LLM for this read query."

    def _read_system_prompt(self) -> str:
        return (
            "You are the OKR read assistant. "
            "Answer using only provided facts. "
            f"Today's date is {self._today_iso()}. Use it for time-relative interpretation. "
            "If no strict match exists, say none found and then provide the closest available rows from fallback context."
        )

    def _read_user_prompt(self, question: str, facts: dict[str, Any]) -> str:
        return f"User question: {question}\n\nRetrieved context:\n{json.dumps(facts, indent=2)}"

    def run_stream(self, question: str, db: Session):
        if not self.llm_client.is_enabled:
            yield self.run(question, db)
            return

        # Regenerate with stream so frontend can render token-by-token.
        # We recompute for parity with run() behavior.
        kr_pairs = (
            db.query(KeyResult, Objective)
            .join(Objective, KeyResult.objective_id == Objective.id)
            .order_by(KeyResult.updated_at.desc())
            .all()
        )
        objectives = db.query(Objective).order_by(Objective.updated_at.desc()).all()
        objective_rows = self._to_objective_rows(objectives)
        kr_rows = self._to_kr_rows(kr_pairs)
        plan = self._infer_query_plan(question)
        entity = plan.get("entity", "both")
        filters = plan.get("filters", {})
        sort_by = plan.get("sort_by")
        sort_order = plan.get("sort_order", "asc")
        limit = plan.get("limit", 50)
        filtered_objectives: list[dict[str, Any]] = []
        filtered_key_results: list[dict[str, Any]] = []
        if entity in {"objective", "both"}:
            filtered_objectives = self._sort_rows(
                self._filter_rows(objective_rows, filters, is_kr=False), sort_by, sort_order
            )[:limit]
        if entity in {"key_result", "both"}:
            filtered_key_results = self._sort_rows(
                self._filter_rows(kr_rows, filters, is_kr=True), sort_by, sort_order
            )[:limit]
        facts = {"query_plan": plan, "objectives": filtered_objectives, "key_results": filtered_key_results}
        if not filtered_objectives and not filtered_key_results:
            facts["objectives"] = objective_rows[: min(30, len(objective_rows))]
            facts["key_results"] = kr_rows[: min(50, len(kr_rows))]
            facts["fallback_mode"] = "broad_context"

        yielded = False
        for chunk in self.llm_client.chat_stream(
            prompt=self._read_user_prompt(question, facts),
            system_prompt=self._read_system_prompt(),
        ):
            yielded = True
            yield chunk
        if not yielded:
            yield self.run(question, db)
