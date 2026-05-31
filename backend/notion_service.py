import logging
import os
from datetime import datetime
from contextlib import contextmanager
from time import perf_counter
from typing import Any

import requests
from sqlalchemy.orm import Session

from models import KeyResult, Objective

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
STATUS_NOT_STARTED = "Not Started"
STATUS_IN_PROGRESS = "In Progress"
STATUS_COMPLETED = "Completed"


@contextmanager
def _timed_step(step_name: str):
    start = perf_counter()
    logger.info("Starting step: %s", step_name)
    try:
        yield
    finally:
        logger.info("Completed step: %s in %.3fs", step_name, perf_counter() - start)


def _headers() -> dict[str, str]:
    token = os.getenv("NOTION_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_database(database_id: str) -> list[dict[str, Any]]:
    step_start = perf_counter()
    url = f"{NOTION_API_BASE}/databases/{database_id}/query"
    results: list[dict[str, Any]] = []
    next_cursor = None
    page_count = 0

    while True:
        page_count += 1
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        request_start = perf_counter()
        resp = requests.post(url, json=payload, headers=_headers(), timeout=20)
        logger.info(
            "Notion query page %s for db %s took %.3fs",
            page_count,
            database_id,
            perf_counter() - request_start,
        )
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        next_cursor = data.get("next_cursor")

    logger.info(
        "Fetched %s rows from db %s in %.3fs",
        len(results),
        database_id,
        perf_counter() - step_start,
    )
    return results


def _prop_text(props: dict[str, Any], name: str) -> str:
    prop = props.get(name, {})
    ptype = prop.get("type")
    if ptype == "title":
        return "".join([x.get("plain_text", "") for x in prop.get("title", [])]).strip()
    if ptype == "rich_text":
        return "".join([x.get("plain_text", "") for x in prop.get("rich_text", [])]).strip()
    return ""


def _prop_select(props: dict[str, Any], name: str) -> str:
    prop = props.get(name, {})
    sel = prop.get("select") or {}
    return sel.get("name", "")


def _prop_multi_select(props: dict[str, Any], name: str) -> str:
    prop = props.get(name, {})
    values = prop.get("multi_select", [])
    if not values:
        return ""
    return ", ".join([x.get("name", "") for x in values if x.get("name")]).strip()


def _prop_people(props: dict[str, Any], name: str) -> str:
    prop = props.get(name, {})
    people = prop.get("people", [])
    if not people:
        return ""
    return people[0].get("name") or people[0].get("id", "")


def _prop_person_like(props: dict[str, Any], name: str) -> str:
    """
    Owner can be modeled as people, rich_text, select, or plain text.
    """
    return (
        _prop_people(props, name)
        or _prop_text(props, name)
        or _prop_select(props, name)
        or _prop_multi_select(props, name)
        or ""
    )


def _prop_number(props: dict[str, Any], name: str) -> float:
    prop = props.get(name, {})
    value = prop.get("number")
    return float(value) if value is not None else 0.0


def _norm_progress(value: float) -> float:
    # Store as 0..1 internally even if Notion keeps 0..100.
    if value > 1:
        return value / 100.0
    return max(0.0, value)


def _prop_date(props: dict[str, Any], name: str):
    prop = props.get(name, {})
    date_val = prop.get("date")
    if not date_val or not date_val.get("start"):
        return None
    try:
        return datetime.fromisoformat(date_val["start"].replace("Z", "+00:00")).date()
    except Exception:
        return None


def _prop_team(props: dict[str, Any]) -> str:
    """
    Team can be modeled differently across Notion DBs.
    Try common shapes in priority order.
    """
    return (
        _prop_select(props, "Team")
        or _prop_multi_select(props, "Team")
        or _prop_text(props, "Team")
    )


def _prop_first_nonempty(props: dict[str, Any], names: list[str], fn) -> Any:
    for n in names:
        v = fn(props, n)
        if v not in ("", None):
            return v
    return None


def _normalize_status(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip().lower()
    if value in {"not started", "not_started", "todo", "to do"}:
        return STATUS_NOT_STARTED
    if value in {"completed", "complete", "done"}:
        return STATUS_COMPLETED
    if value in {
        "in progress",
        "in_progress",
        "started",
        "active",
        "blocked",
        "at risk",
        "delayed",
        "on track",
    }:
        return STATUS_IN_PROGRESS
    return STATUS_IN_PROGRESS


def _derive_objective_status_from_krs(kr_statuses: list[str]) -> str:
    normalized: list[str] = []
    for raw in kr_statuses:
        status = _normalize_status(raw)
        if status is not None:
            normalized.append(status)
    if not normalized:
        return STATUS_NOT_STARTED
    if all(s == STATUS_COMPLETED for s in normalized):
        return STATUS_COMPLETED
    if all(s == STATUS_NOT_STARTED for s in normalized):
        return STATUS_NOT_STARTED
    return STATUS_IN_PROGRESS


def sync_from_notion(db: Session) -> dict[str, int]:
    total_start = perf_counter()
    objectives_db_id = os.getenv("NOTION_OBJECTIVES_DB_ID", "")
    key_results_db_id = os.getenv("NOTION_KEY_RESULTS_DB_ID", "")

    if not objectives_db_id or not key_results_db_id:
        raise ValueError("NOTION_OBJECTIVES_DB_ID and NOTION_KEY_RESULTS_DB_ID are required")

    with _timed_step("Fetch objectives from Notion"):
        objective_pages = _query_database(objectives_db_id)
    with _timed_step("Fetch key results from Notion"):
        kr_pages = _query_database(key_results_db_id)
    objective_notion_ids = {p["id"] for p in objective_pages}
    kr_notion_ids = {p["id"] for p in kr_pages}

    objective_map: dict[str, Objective] = {}
    with _timed_step("Upsert objectives into local DB"):
        for page in objective_pages:
            props = page.get("properties", {})
            notion_id = page["id"]
            title = _prop_text(props, "Objective") or _prop_text(props, "Name") or "Untitled Objective"

            existing = db.query(Objective).filter(Objective.notion_id == notion_id).first()
            if not existing:
                existing = Objective(notion_id=notion_id, title=title)
                db.add(existing)

            existing.title = title
            existing.owner = _prop_person_like(props, "Owner") or existing.owner
            existing.team = _prop_team(props) or existing.team
            existing.quarter = _prop_select(props, "Quarter") or existing.quarter
            existing.status = _normalize_status(_prop_select(props, "Status")) or existing.status
            existing.progress = _norm_progress(_prop_number(props, "Progress"))
            existing.target_date = _prop_first_nonempty(props, ["Target Date", "Due Date"], _prop_date)
            objective_map[notion_id] = existing

    with _timed_step("Flush objective changes"):
        db.flush()

    skipped_kr_without_objective = 0

    with _timed_step("Upsert key results into local DB"):
        for page in kr_pages:
            props = page.get("properties", {})
            notion_id = page["id"]
            title = _prop_text(props, "Key Result") or _prop_text(props, "Name") or "Untitled KR"

            objective_id = None
            objective_relation = props.get("Objective", {}).get("relation", [])
            if objective_relation:
                rel_id = objective_relation[0].get("id")
                rel_obj = objective_map.get(rel_id)
                if rel_obj:
                    objective_id = rel_obj.id

            existing = db.query(KeyResult).filter(KeyResult.notion_id == notion_id).first()
            if not existing:
                if objective_id is None:
                    logger.warning("Skipping new KR with no objective mapping: %s", title)
                    skipped_kr_without_objective += 1
                    continue
                existing = KeyResult(notion_id=notion_id, objective_id=objective_id, title=title)
                db.add(existing)
            elif objective_id is None:
                # Strict mode: keep existing row unchanged when relation is missing.
                logger.warning("Skipping KR update due to missing objective relation: %s", title)
                skipped_kr_without_objective += 1
                continue

            existing.objective_id = objective_id
            existing.title = title
            existing.owner = _prop_person_like(props, "Owner") or existing.owner
            existing.team = _prop_team(props) or existing.team
            existing.risk = _prop_select(props, "Risk") or existing.risk
            existing.status = _normalize_status(_prop_select(props, "Status")) or existing.status
            existing.progress = _norm_progress(_prop_number(props, "Progress"))
            existing.deadline = _prop_first_nonempty(props, ["Deadline", "Due Date"], _prop_date)
            existing.last_update = _prop_date(props, "Last Update") or existing.last_update
            blocker_text = _prop_first_nonempty(props, ["Blocker", "Blocker Notes"], _prop_text) or ""
            existing.blocker_notes = blocker_text or existing.blocker_notes
            status_lower = (existing.status or "").lower()
            checkbox_blocked = bool(props.get("Blocked", {}).get("checkbox", False))
            existing.is_blocked = checkbox_blocked or ("blocked" in status_lower) or bool(blocker_text.strip())

    # Flush ORM updates/inserts before running bulk reconciliation deletes.
    # This avoids stale-row errors when bulk deletes run in the same transaction.
    with _timed_step("Flush key result changes"):
        db.flush()

    with _timed_step("Derive objective status from key result statuses"):
        objectives = db.query(Objective).all()
        for objective in objectives:
            objective.status = _derive_objective_status_from_krs(
                [kr.status for kr in objective.key_results if kr.status]
            )

    # Reconcile deletions:
    # If a row exists locally but is no longer present in Notion DB query results,
    # remove it so dashboard reflects Notion as source of truth.
    with _timed_step("Reconcile local deletions"):
        if kr_notion_ids:
            db.query(KeyResult).filter(~KeyResult.notion_id.in_(kr_notion_ids)).delete(synchronize_session=False)
        if objective_notion_ids:
            db.query(Objective).filter(~Objective.notion_id.in_(objective_notion_ids)).delete(synchronize_session=False)

    with _timed_step("Commit sync transaction"):
        db.commit()
    logger.info("sync_from_notion total duration: %.3fs", perf_counter() - total_start)

    return {
        "objectives_synced": len(objective_pages),
        "key_results_synced": len(kr_pages),
        "key_results_skipped_without_objective": skipped_kr_without_objective,
    }


def _build_select(name: str | None):
    return {"select": {"name": name}} if name else None


def _build_rich_text(value: str | None):
    if not value:
        return None
    return {"rich_text": [{"type": "text", "text": {"content": value}}]}


def _build_title(value: str):
    return {"title": [{"type": "text", "text": {"content": value}}]}


def create_objective_in_notion(
    title: str,
    owner: str | None = None,
    team: str | None = None,
    quarter: str | None = None,
    status: str | None = None,
    progress: float | None = None,
) -> dict[str, Any]:
    objectives_db_id = os.getenv("NOTION_OBJECTIVES_DB_ID", "")
    if not objectives_db_id:
        raise ValueError("NOTION_OBJECTIVES_DB_ID is required")

    url = f"{NOTION_API_BASE}/pages"
    properties: dict[str, Any] = {
        # Works for common DB schemas.
        "Objective": _build_title(title),
    }
    if owner:
        # Owner is commonly rich_text in this template.
        properties["Owner"] = _build_rich_text(owner)
    if team:
        properties["Team"] = _build_select(team)
    if quarter:
        properties["Quarter"] = _build_select(quarter.upper())
    if status:
        properties["Status"] = _build_select(status)
    if progress is not None:
        properties["Progress"] = {"number": progress}

    payload = {
        "parent": {"database_id": objectives_db_id},
        "properties": {k: v for k, v in properties.items() if v is not None},
    }
    resp = requests.post(url, json=payload, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


def create_key_result_in_notion(
    title: str,
    objective_notion_id: str,
    owner: str | None = None,
    team: str | None = None,
    risk: str | None = None,
    status: str | None = None,
    deadline: str | None = None,
    progress: float | None = None,
) -> dict[str, Any]:
    kr_db_id = os.getenv("NOTION_KEY_RESULTS_DB_ID", "")
    if not kr_db_id:
        raise ValueError("NOTION_KEY_RESULTS_DB_ID is required")

    url = f"{NOTION_API_BASE}/pages"
    properties: dict[str, Any] = {
        "Key Result": _build_title(title),
        "Objective": {"relation": [{"id": objective_notion_id}]},
    }
    if owner:
        properties["Owner"] = _build_rich_text(owner)
    if team:
        properties["Team"] = _build_select(team)
    if risk:
        properties["Risk"] = _build_select(risk)
    if status:
        properties["Status"] = _build_select(status)
    if deadline:
        properties["Due Date"] = {"date": {"start": deadline}}
    if progress is not None:
        properties["Progress"] = {"number": progress * 100.0}
    payload = {
        "parent": {"database_id": kr_db_id},
        "properties": {k: v for k, v in properties.items() if v is not None},
    }
    resp = requests.post(url, json=payload, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


def update_objective_in_notion(
    notion_id: str,
    title: str | None = None,
    owner: str | None = None,
    team: str | None = None,
    quarter: str | None = None,
    status: str | None = None,
    progress: float | None = None,
) -> dict[str, Any]:
    url = f"{NOTION_API_BASE}/pages/{notion_id}"
    properties: dict[str, Any] = {}
    if title:
        properties["Objective"] = _build_title(title)
    if owner is not None:
        properties["Owner"] = _build_rich_text(owner) or {"rich_text": []}
    if team is not None:
        properties["Team"] = _build_select(team)
    if quarter is not None:
        properties["Quarter"] = _build_select(quarter.upper() if quarter else None)
    if status is not None:
        properties["Status"] = _build_select(status)
    if progress is not None:
        properties["Progress"] = {"number": progress}

    payload = {"properties": properties}
    resp = requests.patch(url, json=payload, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


def update_key_result_in_notion(
    notion_id: str,
    title: str | None = None,
    objective_notion_id: str | None = None,
    owner: str | None = None,
    team: str | None = None,
    risk: str | None = None,
    status: str | None = None,
    deadline: str | None = None,
    progress: float | None = None,
    blocker_notes: str | None = None,
) -> dict[str, Any]:
    url = f"{NOTION_API_BASE}/pages/{notion_id}"
    properties: dict[str, Any] = {}
    if title:
        properties["Key Result"] = _build_title(title)
    if owner is not None:
        properties["Owner"] = _build_rich_text(owner) or {"rich_text": []}
    if team is not None:
        properties["Team"] = _build_select(team)
    if risk is not None:
        properties["Risk"] = _build_select(risk)
    if status is not None:
        properties["Status"] = _build_select(status)
    if deadline is not None:
        properties["Due Date"] = {"date": {"start": deadline}} if deadline else {"date": None}
    if progress is not None:
        properties["Progress"] = {"number": progress * 100.0}
    if objective_notion_id is not None:
        properties["Objective"] = {"relation": [{"id": objective_notion_id}]}
    if blocker_notes is not None:
        properties["Blocker"] = _build_rich_text(blocker_notes) or {"rich_text": []}

    payload = {"properties": properties}
    resp = requests.patch(url, json=payload, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


def archive_page_in_notion(notion_id: str) -> dict[str, Any]:
    url = f"{NOTION_API_BASE}/pages/{notion_id}"
    payload = {"archived": True}
    resp = requests.patch(url, json=payload, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()
