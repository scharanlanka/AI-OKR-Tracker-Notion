from llm import AzureLLMClient


class RouterAgent:
    """Decides whether user intent is READ or WRITE."""

    def __init__(self, llm_client: AzureLLMClient):
        self.llm_client = llm_client

    def route(self, question: str) -> str:
        if self.llm_client.is_enabled:
            out = self.llm_client.chat(
                system_prompt=(
                    "You classify OKR assistant requests. "
                    "Return only one token: read_agent or write_agent."
                ),
                prompt=f"Question: {question}",
            )
            token = (out or "").strip().lower()
            if token in {"read_agent", "write_agent"}:
                return token

        # Fallback only when LLM routing is unavailable.
        q = question.lower()
        write_keywords = [
            "add", "create", "update", "change", "set", "mark", "edit", "insert", "new objective", "new key result",
        ]
        if any(k in q for k in write_keywords):
            return "write_agent"
        return "read_agent"
