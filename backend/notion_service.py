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


def _prop_people(props: dict[str, Any], name: str) -> str:
    prop = props.get(name, {})
    people = prop.get("people", [])
    if not people:
        return ""
    return people[0].get("name") or people[0].get("id", "")


def _prop_number(props: dict[str, Any], name: str) -> float:
    prop = props.get(name, {})
    value = prop.get("number")
    return float(value) if value is not None else 0.0


def _prop_date(props: dict[str, Any], name: str):
    prop = props.get(name, {})
    date_val = prop.get("date")
    if not date_val or not date_val.get("start"):
        return None
    try:
        return datetime.fromisoformat(date_val["start"].replace("Z", "+00:00")).date()
    except Exception:
        return None


def sync_from_notion(db: Session) -> dict[str, int]:
    objectives_db_id = os.getenv("NOTION_OBJECTIVES_DB_ID", "")
    key_results_db_id = os.getenv("NOTION_KEY_RESULTS_DB_ID", "")

    if not objectives_db_id or not key_results_db_id:
        raise ValueError("NOTION_OBJECTIVES_DB_ID and NOTION_KEY_RESULTS_DB_ID are required")

    objective_pages = _query_database(objectives_db_id)
    kr_pages = _query_database(key_results_db_id)

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
        existing.owner = _prop_people(props, "Owner") or existing.owner
        existing.status = _prop_select(props, "Status") or existing.status
        existing.progress = _prop_number(props, "Progress")
        existing.target_date = _prop_date(props, "Target Date")
        objective_map[notion_id] = existing

    db.flush()

    # Helper by title for simple mock workspace relation if no relation field exists.
    objective_by_title = {obj.title.lower(): obj for obj in objective_map.values()}

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

        if objective_id is None:
            objective_name = _prop_text(props, "Objective Name")
            if objective_name:
                rel_obj = objective_by_title.get(objective_name.lower())
                if rel_obj:
                    objective_id = rel_obj.id

        if objective_id is None and objective_map:
            # Fallback for rough mock data.
            objective_id = next(iter(objective_map.values())).id

        if objective_id is None:
            logger.warning("Skipping KR with no objective mapping: %s", title)
            continue

        existing = db.query(KeyResult).filter(KeyResult.notion_id == notion_id).first()
        if not existing:
            existing = KeyResult(notion_id=notion_id, objective_id=objective_id, title=title)
            db.add(existing)

        existing.objective_id = objective_id
        existing.title = title
        existing.owner = _prop_people(props, "Owner") or existing.owner
        existing.status = _prop_select(props, "Status") or existing.status
        existing.progress = _prop_number(props, "Progress")
        existing.deadline = _prop_date(props, "Deadline")
        existing.is_blocked = bool(props.get("Blocked", {}).get("checkbox", False))
        existing.blocker_notes = _prop_text(props, "Blocker Notes") or existing.blocker_notes

    db.commit()

    return {
        "objectives_synced": len(objective_pages),
        "key_results_synced": len(kr_pages),
    }
