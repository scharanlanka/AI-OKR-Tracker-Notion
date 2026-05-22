from collections import defaultdict
from sqlalchemy.orm import Session

from llm import AzureLLMClient
from models import KeyResult


class TeamSummaryAgent:
    name = "team_agent"

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def run(self, question: str, db: Session) -> str:
        key_results = db.query(KeyResult).all()
        if not key_results:
            return "No key results found to summarize by team member."

        by_owner: dict[str, list[float]] = defaultdict(list)
        blocked_count: dict[str, int] = defaultdict(int)
        for kr in key_results:
            owner = kr.owner or "Unassigned"
            by_owner[owner].append(kr.progress)
            if kr.is_blocked:
                blocked_count[owner] += 1

        lines = []
        for owner, progresses in by_owner.items():
            avg_progress = sum(progresses) / len(progresses)
            lines.append(
                f"- {owner}: KRs={len(progresses)}, avg_progress={avg_progress:.0%}, blocked={blocked_count[owner]}"
            )

        rule_based = "Team summary:\n" + "\n".join(sorted(lines))
        llm_reply = self.llm_client.chat(
            prompt=f"Question: {question}\n\nTeam data:\n{rule_based}\n\nProvide concise team-level observations.",
            system_prompt="You summarize team delivery status from OKR data.",
        )
        return llm_reply or rule_based
