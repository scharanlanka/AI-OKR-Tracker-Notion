import re
from collections import defaultdict
import json
from sqlalchemy.orm import Session

from llm import AzureLLMClient
from models import KeyResult


class ProgressQueryAgent:
    name = "progress_agent"

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def _extract_threshold(self, question: str) -> float:
        # Default threshold for progress checks if none provided.
        default_threshold = 0.8

        # Supports: "80%", "0.8", "80 percent"
        percent_match = re.search(r"(\d{1,3})\s*%", question)
        if percent_match:
            return max(0.0, min(1.0, int(percent_match.group(1)) / 100.0))

        percent_word_match = re.search(r"(\d{1,3})\s*percent", question.lower())
        if percent_word_match:
            return max(0.0, min(1.0, int(percent_word_match.group(1)) / 100.0))

        decimal_match = re.search(r"\b(0(?:\.\d+)?|1(?:\.0+)?)\b", question)
        if decimal_match:
            return max(0.0, min(1.0, float(decimal_match.group(1))))

        return default_threshold

    def _extract_direction(self, question: str) -> str:
        """
        Return one of: below, above.
        Defaults to below for risk-style progress questions.
        """
        q = question.lower()
        if any(x in q for x in ["above", "over", "greater", "at least", "more than"]):
            return "above"
        return "below"

    def run(self, question: str, db: Session) -> str:
        key_results = db.query(KeyResult).all()
        if not key_results:
            return "I could not find any key results to analyze progress."

        by_owner: dict[str, list[float]] = defaultdict(list)
        for kr in key_results:
            by_owner[kr.owner or "Unassigned"].append(kr.progress)

        team_progress = []
        for owner, vals in by_owner.items():
            avg = sum(vals) / len(vals)
            team_progress.append({"owner": owner, "avg_progress": avg, "kr_count": len(vals)})

        threshold = self._extract_threshold(question)
        direction = self._extract_direction(question)

        if direction == "below":
            filtered = sorted([x for x in team_progress if x["avg_progress"] < threshold], key=lambda x: x["avg_progress"])
            heading = f"Teams below {int(threshold * 100)}% progress"
        else:
            filtered = sorted([x for x in team_progress if x["avg_progress"] >= threshold], key=lambda x: x["avg_progress"], reverse=True)
            heading = f"Teams at or above {int(threshold * 100)}% progress"

        if not self.llm_client.is_enabled:
            return (
                "LLM is not configured. Set AZURE_LLM_ENDPOINT, AZURE_LLM_API_KEY, and "
                "AZURE_LLM_DEPLOYMENT_NAME to enable natural-language progress answers."
            )

        payload = {
            "question": question,
            "metric": heading,
            "threshold_percent": int(threshold * 100),
            "direction": direction,
            "teams": [
                {
                    "name": x["owner"],
                    "avg_progress_percent": round(x["avg_progress"] * 100, 1),
                    "kr_count": x["kr_count"],
                }
                for x in filtered
            ],
        }

        llm_reply = self.llm_client.chat(
            prompt=(
                "Use this JSON data to answer the user.\n"
                "Return normal chat text, but include team names clearly.\n"
                "If no teams match, say that directly.\n"
                "Do not invent teams.\n\n"
                f"{json.dumps(payload, indent=2)}"
            ),
            system_prompt="You are an OKR assistant. Keep answers clear and conversational.",
        )
        if llm_reply:
            return llm_reply

        return (
            "I could not get an LLM response for this progress query. "
            "Please check Azure LLM credentials or endpoint configuration."
        )
