from sqlalchemy.orm import Session

from llm import AzureLLMClient
from models import KeyResult, Objective


class BlockerSummaryAgent:
    name = "blocker_agent"

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def run(self, question: str, db: Session) -> str:
        rows = (
            db.query(KeyResult, Objective)
            .join(Objective, KeyResult.objective_id == Objective.id)
            .filter(KeyResult.is_blocked.is_(True))
            .all()
        )

        if not rows:
            return "No blocked key results right now."

        lines = [
            f"- {kr.title} ({obj.title}) owner={kr.owner or 'N/A'} notes={kr.blocker_notes or 'N/A'}"
            for kr, obj in rows[:10]
        ]
        rule_based = "Blocked key results:\n" + "\n".join(lines)

        llm_reply = self.llm_client.chat(
            prompt=f"Question: {question}\n\nBlocked items:\n{rule_based}\n\nProvide concise unblock suggestions.",
            system_prompt="You are an OKR delivery coach.",
        )
        return llm_reply or rule_based
