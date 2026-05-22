from sqlalchemy.orm import Session

from llm import AzureLLMClient
from okr_service import get_risks


class RiskAnalysisAgent:
    name = "risk_agent"

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def run(self, question: str, db: Session) -> str:
        risks = get_risks(db)
        if not risks:
            return "No major OKR risks detected right now."

        summary_lines = [
            f"- {r['key_result_title']} ({r['objective_title']}): progress={r['progress']:.0%}, blocked={r['is_blocked']}, deadline={r['deadline']}"
            for r in risks[:10]
        ]
        rule_based = "Top risks:\n" + "\n".join(summary_lines)

        llm_reply = self.llm_client.chat(
            prompt=f"Question: {question}\n\nRisk data:\n{rule_based}\n\nGive a concise risk summary with actions.",
            system_prompt="You are an OKR risk analyst. Keep it brief and practical.",
        )
        return llm_reply or rule_based
