from sqlalchemy.orm import Session

from llm import AzureLLMClient
from models import KeyResult, Objective


class GeneralOKRAgent:
    name = "general_agent"

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def run(self, question: str, db: Session) -> str:
        objectives = db.query(Objective).count()
        key_results = db.query(KeyResult).count()

        avg_progress = 0.0
        if key_results:
            total = sum(kr.progress for kr in db.query(KeyResult).all())
            avg_progress = total / key_results

        rule_based = (
            f"Snapshot: objectives={objectives}, key_results={key_results}, "
            f"average_kr_progress={avg_progress:.0%}."
        )

        llm_reply = self.llm_client.chat(
            prompt=f"Question: {question}\n\nData:\n{rule_based}\n\nAnswer briefly.",
            system_prompt="You are a helpful OKR assistant.",
        )
        return llm_reply or rule_based
