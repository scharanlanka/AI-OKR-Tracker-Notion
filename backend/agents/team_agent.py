from collections import defaultdict
import re
from sqlalchemy.orm import Session

from llm import AzureLLMClient
from models import KeyResult


class TeamSummaryAgent:
    name = "team_agent"

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def _extract_threshold(self, question: str) -> float | None:
        """
        Extract percentage thresholds from natural language.
        Example: "below 50% progress" -> 0.5
        """
        match = re.search(r"(\d{1,3})\s*%", question)
        if not match:
            return None
        value = max(0, min(100, int(match.group(1))))
        return value / 100.0

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

        summary_rows = []
        for owner, progresses in by_owner.items():
            avg_progress = sum(progresses) / len(progresses)
            summary_rows.append(
                {
                    "owner": owner,
                    "kr_count": len(progresses),
                    "avg_progress": avg_progress,
                    "blocked": blocked_count[owner],
                }
            )

        threshold = self._extract_threshold(question)
        q_lower = question.lower()
        asks_below = any(
            phrase in q_lower
            for phrase in [
                "below",
                "under",
                "less than",
                "not met",
                "not even",
                "haven't met",
                "hasn't met",
                "didn't meet",
                "not meeting",
                "underperform",
            ]
        )

        if threshold is not None and asks_below:
            filtered = sorted([x for x in summary_rows if x["avg_progress"] < threshold], key=lambda x: x["avg_progress"])
            if not filtered:
                rule_based = f"No teams are below {int(threshold * 100)}% average progress."
            else:
                lines = [
                    f"- {x['owner']}: avg_progress={x['avg_progress']:.0%}, KRs={x['kr_count']}, blocked={x['blocked']}"
                    for x in filtered
                ]
                rule_based = f"Teams below {int(threshold * 100)}% average progress:\n" + "\n".join(lines)
        else:
            lines = [
                f"- {x['owner']}: KRs={x['kr_count']}, avg_progress={x['avg_progress']:.0%}, blocked={x['blocked']}"
                for x in sorted(summary_rows, key=lambda x: x["owner"].lower())
            ]
            rule_based = "Team summary:\n" + "\n".join(lines)

        llm_reply = self.llm_client.chat(
            prompt=f"Question: {question}\n\nTeam data:\n{rule_based}\n\nProvide concise team-level observations.",
            system_prompt="You summarize team delivery status from OKR data.",
        )
        return llm_reply or rule_based
