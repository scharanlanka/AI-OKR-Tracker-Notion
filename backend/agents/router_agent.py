class RouterAgent:
    """Simple keyword router for Sprint 1."""

    def route(self, question: str) -> str:
        q = question.lower()
        if any(k in q for k in ["risk", "at risk", "danger"]):
            return "risk_agent"
        if any(k in q for k in ["deadline", "due", "timeline"]):
            return "deadline_agent"
        if any(k in q for k in ["blocker", "blocked", "stuck"]):
            return "blocker_agent"
        if any(k in q for k in ["team", "owner", "who"]):
            return "team_agent"
        return "general_agent"
