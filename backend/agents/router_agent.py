from llm import AzureLLMClient


class RouterAgent:
    """Decides whether user intent is READ or WRITE."""

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def route(self, question: str) -> str:
        if self.llm_client.is_enabled:
            out = self.llm_client.chat(
                system_prompt=(
                    "You route OKR assistant requests by user intent.\n"
                    "Return exactly one token: read_agent or write_agent.\n"
                    "Use write_agent for create/add/update/edit/modify/delete/archive actions.\n"
                    "Use read_agent for lookup/questions/summaries/listing/status checks.\n"
                    "If ambiguous, default to read_agent."
                ),
                prompt=f"Question: {question}",
            )
            token = (out or "").strip().lower()
            if token in {"read_agent", "write_agent"}:
                return token

        # Fallback only when LLM routing is unavailable or returns invalid output.
        # Keep this intentionally minimal to avoid hardwired routing logic.
        q = question.lower()
        write_keywords = ["create", "add", "update", "edit", "modify", "delete", "remove"]
        if any(k in q for k in write_keywords):
            return "write_agent"
        return "read_agent"
