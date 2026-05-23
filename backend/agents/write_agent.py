import re
from datetime import datetime
from sqlalchemy.orm import Session

from llm import AzureLLMClient
from notion_service import create_key_result_in_notion, create_objective_in_notion


class WriteAgent:
    """Executes create/update intent on Notion and reports result."""

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def _extract_value(self, text: str, field: str) -> str | None:
        # Supports patterns like: title: ..., owner: ..., objective: ...
        m = re.search(rf"{field}\s*:\s*([^,\n]+)", text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else None

    def _extract_quoted_title(self, text: str) -> str | None:
        m = re.search(r'"([^"]+)"', text)
        return m.group(1).strip() if m else None

    def _extract_owner_phrase(self, text: str) -> str | None:
        m = re.search(
            r"owned by\s+(.+?)(?:\s+by\s+\w+\s+team|\s+on\s+\w+\s+team|\s+in\s+q[1-4]|\s+with\s+|\s+the\s+status|\s+due\s+on|\s+progress|,|\.|$)",
            text,
            flags=re.IGNORECASE,
        )
        return m.group(1).strip() if m else None

    def _extract_team_phrase(self, text: str) -> str | None:
        m = re.search(r"(frontend|backend|platform|growth|customer|security|product)\s+team", text, flags=re.IGNORECASE)
        if not m:
            return None
        return f"{m.group(1).capitalize()} Team"

    def _extract_quarter(self, text: str) -> str | None:
        m = re.search(r"\bq([1-4])\b", text, flags=re.IGNORECASE)
        if not m:
            return None
        return f"Q{m.group(1)}"

    def _extract_status(self, text: str) -> str | None:
        q = text.lower()
        if "not started" in q:
            return "Not Started"
        if "in progress" in q:
            return "In Progress"
        if "blocked" in q:
            return "Blocked"
        if "at risk" in q:
            return "At Risk"
        if "on track" in q:
            return "On Track"
        if "off track" in q:
            return "Off Track"
        if "planned" in q:
            return "Planned"
        return None

    def _extract_progress(self, text: str) -> float | None:
        m = re.search(r"(\d{1,3})\s*%", text)
        if not m:
            return None
        return max(0.0, min(1.0, int(m.group(1)) / 100.0))

    def _extract_risk(self, text: str) -> str | None:
        q = text.lower()
        if "high risk" in q:
            return "High"
        if "medium risk" in q:
            return "Medium"
        if "low risk" in q:
            return "Low"
        if "delayed" in q:
            return "Delayed"
        return None

    def _extract_due_date_iso(self, text: str) -> str | None:
        # Supports formats like "5th june 2026", "5 june 2026", "2026-06-05"
        t = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text, flags=re.IGNORECASE)

        m_iso = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", t)
        if m_iso:
            return m_iso.group(1)

        m_words = re.search(
            r"\b(\d{1,2})\s+"
            r"(january|february|march|april|may|june|july|august|september|october|november|december)"
            r"\s+(\d{4})\b",
            t,
            flags=re.IGNORECASE,
        )
        if m_words:
            try:
                dt = datetime.strptime(f"{m_words.group(1)} {m_words.group(2)} {m_words.group(3)}", "%d %B %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return None

        return None

    def _extract_objective_ref(self, text: str) -> str | None:
        m = re.search(r"\bfor\s+objective\s+\"([^\"]+)\"", text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(r"\bunder\s+objective\s+\"([^\"]+)\"", text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    def run(self, question: str, db: Session) -> str:
        q = question.lower()

        if "objective" in q and any(x in q for x in ["create", "add", "new"]):
            title = (
                self._extract_value(question, "title")
                or self._extract_quoted_title(question)
                or question.replace("create objective", "").replace("add objective", "").strip()
            )
            owner = self._extract_value(question, "owner") or self._extract_owner_phrase(question)
            team = self._extract_value(question, "team") or self._extract_team_phrase(question)
            quarter = self._extract_value(question, "quarter") or self._extract_quarter(question)
            status = self._extract_value(question, "status") or self._extract_status(question)
            progress = self._extract_progress(question)

            created = create_objective_in_notion(
                title=title,
                owner=owner,
                team=team,
                quarter=quarter,
                status=status,
                progress=progress,
            )
            return (
                f"Added objective '{title}' to Notion "
                f"(owner={owner or 'N/A'}, team={team or 'N/A'}, quarter={quarter or 'N/A'}, status={status or 'N/A'}). "
                f"Notion page id: {created.get('id', 'unknown')}."
            )

        if any(x in q for x in ["key result", "kr"]) and any(x in q for x in ["create", "add", "new"]):
            title = (
                self._extract_value(question, "title")
                or self._extract_quoted_title(question)
                or question.replace("create key result", "").replace("add key result", "").strip()
            )
            owner = self._extract_value(question, "owner") or self._extract_owner_phrase(question)
            team = self._extract_value(question, "team") or self._extract_team_phrase(question)
            risk = self._extract_value(question, "risk") or self._extract_risk(question)
            status = self._extract_value(question, "status") or self._extract_status(question)
            progress = self._extract_progress(question)
            deadline = self._extract_due_date_iso(question)
            objective_name = self._extract_value(question, "objective") or self._extract_objective_ref(question)

            created = create_key_result_in_notion(
                title=title,
                objective_name=objective_name,
                owner=owner,
                team=team,
                risk=risk,
                status=status,
                deadline=deadline,
                progress=progress,
            )
            return (
                f"Added key result '{title}' to Notion "
                f"(owner={owner or 'N/A'}, team={team or 'N/A'}, risk={risk or 'N/A'}, status={status or 'N/A'}, due={deadline or 'N/A'}). "
                f"Notion page id: {created.get('id', 'unknown')}."
            )

        return (
            "I can write to Notion for create/add actions. "
            "Try: 'create objective title: Improve onboarding, owner: Alice, status: On Track'."
        )
