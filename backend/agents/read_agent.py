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

    def _normalize(self, text: str | None) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip().lower()

    def _row_text(self, row: dict) -> str:
        parts = [
            row.get("objective_title", ""),
            row.get("title", ""),
            row.get("owner", ""),
            row.get("team", ""),
            row.get("risk", ""),
            row.get("status", ""),
            row.get("deadline", ""),
            row.get("last_update", ""),
            row.get("blocker", ""),
            "blocked" if row.get("blocked") else "",
            f"{int((row.get('progress', 0.0) or 0.0) * 100)}%",
        ]
        return self._normalize(" ".join(str(x) for x in parts if x is not None))

    def _extract_search_terms(self, question: str) -> list[str]:
        q = self._normalize(question)
        stop = {
            "what", "which", "who", "show", "list", "all", "the", "a", "an", "is", "are", "with", "and", "or",
            "of", "for", "to", "in", "on", "by", "their", "its", "that", "this", "these", "those", "please",
            "key", "result", "results", "objective", "objectives", "progress", "status", "risk", "team", "owner",
            "deadline", "deadlines", "due", "blocker", "blockers", "quarter",
        }
        tokens = [t for t in re.split(r"[^a-z0-9%]+", q) if t and t not in stop]

        # Include candidate owner/team phrases.
        phrases = re.findall(r"\b[a-z]+(?:\s+[a-z]+){1,2}\b", q)
        terms = set(tokens)
        for p in phrases:
            if len(p.split()) >= 2:
                terms.add(p)
        return sorted(terms)

    def _has_entity_phrase(self, question: str) -> bool:
        q = self._normalize(question)
        # Two+ token natural phrase likely referring to person/objective/team label.
        return bool(re.search(r"\b[a-z]+(?:\s+[a-z]+){1,3}\b", q))

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
        retrieval = {"query": question, "hop": 1, "facts": []}

        kr_rows = (
            db.query(KeyResult, Objective)
            .join(Objective, KeyResult.objective_id == Objective.id)
            .order_by(KeyResult.updated_at.desc())
            .all()
        )
        flat_rows = [
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
                "blocked": kr.is_blocked,
                "blocker": kr.blocker_notes,
            }
            for kr, obj in kr_rows
        ]
        all_objectives = db.query(Objective).order_by(Objective.updated_at.desc()).all()

        # Hop 1: targeted retrieval.
        # Prioritize entity/person queries first so "owner + progress" questions
        # return concrete KR rows instead of aggregate summaries.
        if self._has_entity_phrase(question):
            terms = self._extract_search_terms(question)
            matched = []
            for row in flat_rows:
                haystack = self._row_text(row)
                if all(t in haystack for t in terms) or any(t in haystack for t in terms):
                    matched.append(row)

            qn = self._normalize(question)
            boosted = sorted(
                matched,
                key=lambda r: (
                    0 if self._normalize(r.get("owner")) and self._normalize(r.get("owner")) in qn else 1,
                    0 if self._normalize(r.get("objective_title")) and self._normalize(r.get("objective_title")) in qn else 1,
                    0 if self._normalize(r.get("team")) and self._normalize(r.get("team")) in qn else 1,
                ),
            )

            retrieval["facts"] = {
                "query_terms": terms,
                "matched_key_results": boosted[:80],
            }
        elif self._is_deadline_query(question):
            today = date.today()
            rows = [r for r in flat_rows if r["deadline"] and r["deadline"] >= str(today)]
            rows.sort(key=lambda r: r["deadline"] or "9999-12-31")
            retrieval["facts"] = {
                "today": str(today),
                "upcoming_key_results": rows[:100],
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
            if team_phrase:
                p = team_phrase.lower()
                matched_obj = [o for o in all_objectives if o.team and p in o.team.lower()]
            else:
                matched_obj = [o for o in all_objectives if o.team]

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
            terms = self._extract_search_terms(question)
            matched = []
            for row in flat_rows:
                haystack = self._row_text(row)
                if all(t in haystack for t in terms) or any(t in haystack for t in terms):
                    matched.append(row)

            # Boost strong owner/objective exact-ish matches for person/entity questions.
            qn = self._normalize(question)
            boosted = sorted(
                matched,
                key=lambda r: (
                    0 if self._normalize(r.get("owner")) and self._normalize(r.get("owner")) in qn else 1,
                    0 if self._normalize(r.get("objective_title")) and self._normalize(r.get("objective_title")) in qn else 1,
                ),
            )

            retrieval["facts"] = {
                "query_terms": terms,
                "matched_key_results": boosted[:80],
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
                    for x in all_objectives[:40]
                ],
            }

        # Hop 2: broaden if first hop is sparse.
        sparse = not retrieval["facts"] or (isinstance(retrieval["facts"], list) and len(retrieval["facts"]) <= 1)
        if sparse:
            retrieval["hop"] = 2
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
                    for o in all_objectives
                ],
                "key_results": flat_rows,
            }

        if not self.llm_client.is_enabled:
            facts = retrieval["facts"]
            if isinstance(facts, dict) and "matched_key_results" in facts:
                rows = facts["matched_key_results"][:12]
                if not rows:
                    return "No matching key results found."
                return "\n".join(
                    [
                        f"- {r['title']} ({r['objective_title']}) owner={r.get('owner') or 'N/A'} "
                        f"team={r.get('team') or 'N/A'} progress={int((r.get('progress') or 0)*100)}% "
                        f"status={r.get('status') or 'N/A'} risk={r.get('risk') or 'N/A'}"
                        for r in rows
                    ]
                )
            return "Read query processed, but LLM is disabled."

        response = self.llm_client.chat(
            system_prompt=(
                "You are the OKR read assistant. "
                "Answer naturally using only provided facts. "
                "When user asks for teams/names, explicitly list the names. "
                "If no match exists, say none found. "
                "When rows are provided, prefer exact field matches across owner/team/risk/status/progress/deadline/blocker/title."
            ),
            prompt=(
                f"User question: {question}\n\n"
                f"Retrieved context (multi-hop={retrieval['hop']}):\n"
                f"{json.dumps(retrieval['facts'], indent=2)}"
            ),
        )

        return response or "I could not generate a response from LLM for this read query."
