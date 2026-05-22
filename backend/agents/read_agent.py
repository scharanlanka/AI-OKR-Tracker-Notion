from collections import defaultdict
from datetime import date
import json
import re
from sqlalchemy.orm import Session

from llm import AzureLLMClient
from models import KeyResult, Objective


class ReadAgent:
    """
    Stateful read agent with multi-hop retrieval:
    1) infer query focus
    2) fetch matching rows
    3) if sparse, broaden retrieval
    4) answer with LLM from retrieved facts
    """

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def _extract_threshold(self, question: str) -> float | None:
        m = re.search(r"(\d{1,3})\s*%", question)
        if not m:
            return None
        return max(0.0, min(1.0, int(m.group(1)) / 100.0))

    def _is_progress_query(self, question: str) -> bool:
        q = question.lower()
        return any(x in q for x in ["progress", "%", "percent", "below", "above", "met", "underperform"])

    def _is_team_query(self, question: str) -> bool:
        q = question.lower()
        return "team" in q or "assigned to" in q

    def _is_deadline_query(self, question: str) -> bool:
        q = question.lower()
        return any(x in q for x in ["deadline", "deadlines", "due", "upcoming", "next"])

    def _extract_team_phrase(self, question: str) -> str | None:
        q = question.lower()
        m = re.search(r"assigned to\\s+the\\s+(.+?)\\??$", q)
        if m:
            return m.group(1).strip()
        m = re.search(r"for\\s+the\\s+(.+?)\\??$", q)
        if m:
            return m.group(1).strip()
        m = re.search(r"(.+?)\\s+team", q)
        if m:
            return (m.group(1).strip() + " team").strip()
        return None

    def _team_progress_rows(self, db: Session):
        by_team: dict[str, list[float]] = defaultdict(list)
        for kr in db.query(KeyResult).all():
            by_team[kr.team or kr.owner or "Unassigned"].append(kr.progress)
        rows = []
        for team, values in by_team.items():
            rows.append(
                {
                    "team": team,
                    "avg_progress": round(sum(values) / len(values), 4),
                    "kr_count": len(values),
                }
            )
        return rows

    def run(self, question: str, db: Session) -> str:
        if not self.llm_client.is_enabled:
            return "LLM is required for read-agent responses. Please configure Azure LLM variables."

        retrieval = {"query": question, "hop": 1, "facts": []}

        # Hop 1: targeted retrieval.
        if self._is_deadline_query(question):
            today = date.today()
            rows = (
                db.query(KeyResult)
                .filter(KeyResult.deadline.isnot(None), KeyResult.deadline >= today)
                .order_by(KeyResult.deadline.asc())
                .limit(100)
                .all()
            )
            retrieval["facts"] = {
                "today": str(today),
                "upcoming_key_results": [
                    {
                        "title": r.title,
                        "owner": r.owner,
                        "team": r.team,
                        "status": r.status,
                        "progress": r.progress,
                        "deadline": str(r.deadline) if r.deadline else None,
                        "risk": r.risk,
                        "blocked": r.is_blocked,
                    }
                    for r in rows
                ],
            }
        elif self._is_progress_query(question):
            rows = self._team_progress_rows(db)
            threshold = self._extract_threshold(question)
            if threshold is not None:
                q = question.lower()
                if any(x in q for x in ["above", "over", "at least"]):
                    rows = [r for r in rows if r["avg_progress"] >= threshold]
                else:
                    rows = [r for r in rows if r["avg_progress"] < threshold]
            retrieval["facts"] = rows[:30]
        elif self._is_team_query(question):
            team_phrase = self._extract_team_phrase(question)
            all_obj = db.query(Objective).order_by(Objective.updated_at.desc()).all()
            if team_phrase:
                p = team_phrase.lower()
                matched_obj = [o for o in all_obj if o.team and p in o.team.lower()]
            else:
                matched_obj = [o for o in all_obj if o.team]

            retrieval["facts"] = {
                "team_filter": team_phrase,
                "objectives": [
                    {
                        "title": o.title,
                        "owner": o.owner,
                        "team": o.team,
                        "quarter": o.quarter,
                        "status": o.status,
                        "progress": o.progress,
                    }
                    for o in matched_obj[:50]
                ],
            }
        else:
            obj_rows = db.query(Objective).order_by(Objective.updated_at.desc()).limit(20).all()
            kr_rows = db.query(KeyResult).order_by(KeyResult.updated_at.desc()).limit(40).all()
            retrieval["facts"] = {
                "objectives": [
                    {
                        "title": x.title,
                        "owner": x.owner,
                        "team": x.team,
                        "quarter": x.quarter,
                        "status": x.status,
                        "progress": x.progress,
                        "target_date": str(x.target_date) if x.target_date else None,
                    }
                    for x in obj_rows
                ],
                "key_results": [
                    {
                        "title": x.title,
                        "owner": x.owner,
                        "team": x.team,
                        "risk": x.risk,
                        "status": x.status,
                        "progress": x.progress,
                        "deadline": str(x.deadline) if x.deadline else None,
                        "last_update": str(x.last_update) if x.last_update else None,
                        "blocked": x.is_blocked,
                        "blocker": x.blocker_notes,
                    }
                    for x in kr_rows
                ],
            }

        # Hop 2: broaden if first hop is sparse.
        sparse = not retrieval["facts"] or (isinstance(retrieval["facts"], list) and len(retrieval["facts"]) <= 1)
        if sparse:
            retrieval["hop"] = 2
            all_obj = db.query(Objective).all()
            all_kr = db.query(KeyResult).all()
            retrieval["facts"] = {
                "objectives": [
                    {
                        "title": o.title,
                        "owner": o.owner,
                        "team": o.team,
                        "quarter": o.quarter,
                        "status": o.status,
                        "progress": o.progress,
                    }
                    for o in all_obj
                ],
                "key_results": [
                    {
                        "title": k.title,
                        "owner": k.owner,
                        "team": k.team,
                        "risk": k.risk,
                        "status": k.status,
                        "progress": k.progress,
                        "blocked": k.is_blocked,
                        "blocker": k.blocker_notes,
                        "deadline": str(k.deadline) if k.deadline else None,
                        "last_update": str(k.last_update) if k.last_update else None,
                    }
                    for k in all_kr
                ],
            }

        response = self.llm_client.chat(
            system_prompt=(
                "You are the OKR read assistant. "
                "Answer naturally using only provided facts. "
                "When user asks for teams/names, explicitly list the names. "
                "If no match exists, say none found."
            ),
            prompt=(
                f"User question: {question}\n\n"
                f"Retrieved context (multi-hop={retrieval['hop']}):\n"
                f"{json.dumps(retrieval['facts'], indent=2)}"
            ),
        )

        return response or "I could not generate a response from LLM for this read query."
