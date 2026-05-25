import logging
import os
from datetime import datetime
from typing import Any

import requests
from sqlalchemy.orm import Session

from models import KeyResult, Objective

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict[str, str]:
    token = os.getenv("NOTION_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_database(database_id: str) -> list[dict[str, Any]]:
    url = f"{NOTION_API_BASE}/databases/{database_id}/query"
    results: list[dict[str, Any]] = []
    next_cursor = None

    while True:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        resp = requests.post(url, json=payload, headers=_headers(), timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        next_cursor = data.get("next_cursor")

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


def sync_from_notion(db: Session) -> dict[str, int]:
    objectives_db_id = os.getenv("NOTION_OBJECTIVES_DB_ID", "")
    key_results_db_id = os.getenv("NOTION_KEY_RESULTS_DB_ID", "")

    if not objectives_db_id or not key_results_db_id:
        raise ValueError("NOTION_OBJECTIVES_DB_ID and NOTION_KEY_RESULTS_DB_ID are required")

    objective_pages = _query_database(objectives_db_id)
    kr_pages = _query_database(key_results_db_id)
    objective_notion_ids = {p["id"] for p in objective_pages}
    kr_notion_ids = {p["id"] for p in kr_pages}

    objective_map: dict[str, Objective] = {}
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
        existing.status = _prop_select(props, "Status") or existing.status
        existing.progress = _norm_progress(_prop_number(props, "Progress"))
        existing.target_date = _prop_first_nonempty(props, ["Target Date", "Due Date"], _prop_date)
        objective_map[notion_id] = existing

    db.flush()

    # Helper by title for simple mock workspace relation if no relation field exists.
    objective_by_title = {obj.title.lower(): obj for obj in objective_map.values()}

    for page in kr_pages:
        props = page.get("properties", {})
        notion_id = page["id"]
        title = _prop_text(props, "Key Result") or _prop_text(props, "Name") or "Untitled KR"
        kr_team = _prop_team(props)

        objective_id = None
        objective_relation = props.get("Objective", {}).get("relation", [])
        if objective_relation:
            rel_id = objective_relation[0].get("id")
            rel_obj = objective_map.get(rel_id)
            if rel_obj:
                objective_id = rel_obj.id

        if objective_id is None:
            objective_name = _prop_text(props, "Objective Name")
            if objective_name:
                rel_obj = objective_by_title.get(objective_name.lower())
                if rel_obj:
                    objective_id = rel_obj.id

        if objective_id is None:
            # Heuristic repair: map "Objective title - KR X" to objective title.
            # Example: "Improve onboarding completion rate - KR 2" -> "Improve onboarding completion rate"
            lower_title = title.lower()
            if " - kr" in lower_title:
                guessed_objective_title = title[: lower_title.index(" - kr")].strip().lower()
                rel_obj = objective_by_title.get(guessed_objective_title)
                if rel_obj:
                    objective_id = rel_obj.id

        if objective_id is None and kr_team:
            # Fallback: if exactly one objective matches KR team, attach to it.
            team_matches = [
                obj for obj in objective_map.values()
                if (obj.team or "").strip().lower() == kr_team.strip().lower()
            ]
            if len(team_matches) == 1:
                objective_id = team_matches[0].id

        if objective_id is None and objective_map:
            # Last-resort fallback to keep KR visible instead of skipping sync.
            # Prefer the most recently created objective id in the local DB snapshot.
            objective_id = max(objective_map.values(), key=lambda o: o.id or 0).id

        existing = db.query(KeyResult).filter(KeyResult.notion_id == notion_id).first()
        if not existing:
            if objective_id is None:
                logger.warning("Skipping new KR with no objective mapping: %s", title)
                continue
            existing = KeyResult(notion_id=notion_id, objective_id=objective_id, title=title)
            db.add(existing)
        elif objective_id is None:
            # Preserve previous objective link if current payload doesn't provide one.
            objective_id = existing.objective_id

        existing.objective_id = objective_id
        existing.title = title
        existing.owner = _prop_person_like(props, "Owner") or existing.owner
        existing.team = _prop_team(props) or existing.team
        existing.risk = _prop_select(props, "Risk") or existing.risk
        existing.status = _prop_select(props, "Status") or existing.status
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
    db.flush()

    # Reconcile deletions:
    # If a row exists locally but is no longer present in Notion DB query results,
    # remove it so dashboard reflects Notion as source of truth.
    if kr_notion_ids:
        db.query(KeyResult).filter(~KeyResult.notion_id.in_(kr_notion_ids)).delete(synchronize_session=False)
    if objective_notion_ids:
        db.query(Objective).filter(~Objective.notion_id.in_(objective_notion_ids)).delete(synchronize_session=False)

    db.commit()

    return {
        "objectives_synced": len(objective_pages),
        "key_results_synced": len(kr_pages),
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
    objective_name: str | None = None,
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
    if objective_name:
        # Fallback-friendly field if no relation id is provided.
        properties["Objective Name"] = _build_rich_text(objective_name)

    payload = {
        "parent": {"database_id": kr_db_id},
        "properties": {k: v for k, v in properties.items() if v is not None},
    }
    resp = requests.post(url, json=payload, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()
