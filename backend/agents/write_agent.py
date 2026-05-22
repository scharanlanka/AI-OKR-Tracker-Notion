import re
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

    def run(self, question: str, db: Session) -> str:
        q = question.lower()

        if "objective" in q and any(x in q for x in ["create", "add", "new"]):
            title = self._extract_value(question, "title") or question.replace("create objective", "").strip()
            owner = self._extract_value(question, "owner")
            status = self._extract_value(question, "status")
            progress_str = self._extract_value(question, "progress")
            progress = float(progress_str.replace("%", "")) / 100.0 if progress_str and "%" in progress_str else None

            created = create_objective_in_notion(title=title, owner=owner, status=status, progress=progress)
            return f"Added objective '{title}' to Notion. Notion page id: {created.get('id', 'unknown')}."

        if any(x in q for x in ["key result", "kr"]) and any(x in q for x in ["create", "add", "new"]):
            title = self._extract_value(question, "title") or question.replace("create key result", "").strip()
            owner = self._extract_value(question, "owner")
            status = self._extract_value(question, "status")
            objective_name = self._extract_value(question, "objective")

            created = create_key_result_in_notion(title=title, objective_name=objective_name, owner=owner, status=status)
            return f"Added key result '{title}' to Notion. Notion page id: {created.get('id', 'unknown')}."

        return (
            "I can write to Notion for create/add actions. "
            "Try: 'create objective title: Improve onboarding, owner: Alice, status: On Track'."
        )
