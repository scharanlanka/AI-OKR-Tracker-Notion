from sqlalchemy.orm import Session

from llm import AzureLLMClient
from okr_service import get_upcoming_deadlines


class DeadlineAgent:
    name = "deadline_agent"

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def run(self, question: str, db: Session) -> str:
        items = get_upcoming_deadlines(db, days=14)
        if not items:
            return "No key result deadlines in the next 14 days."

        lines = [
            f"- {x['deadline']}: {x['key_result_title']} ({x['objective_title']}) progress={x['progress']:.0%}"
            for x in items[:10]
        ]
        rule_based = "Upcoming deadlines:\n" + "\n".join(lines)

        llm_reply = self.llm_client.chat(
            prompt=f"Question: {question}\n\nDeadline data:\n{rule_based}\n\nProvide concise prioritization.",
            system_prompt="You are an OKR deadline assistant.",
        )
        return llm_reply or rule_based
