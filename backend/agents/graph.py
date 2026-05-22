from typing import TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from agents.blocker_agent import BlockerSummaryAgent
from agents.deadline_agent import DeadlineAgent
from agents.general_agent import GeneralOKRAgent
from agents.risk_agent import RiskAnalysisAgent
from agents.router_agent import RouterAgent
from agents.team_agent import TeamSummaryAgent
from llm import AzureLLMClient


class AgentState(TypedDict):
    question: str
    route: str
    answer: str
    db: Session


class OKRGraph:
    def __init__(self):
        llm_client = AzureLLMClient()
        self.router = RouterAgent()
        self.risk_agent = RiskAnalysisAgent(llm_client)
        self.deadline_agent = DeadlineAgent(llm_client)
        self.blocker_agent = BlockerSummaryAgent(llm_client)
        self.team_agent = TeamSummaryAgent(llm_client)
        self.general_agent = GeneralOKRAgent(llm_client)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("router_node", self._route)
        workflow.add_node("risk_agent", self._risk)
        workflow.add_node("deadline_agent", self._deadline)
        workflow.add_node("blocker_agent", self._blocker)
        workflow.add_node("team_agent", self._team)
        workflow.add_node("general_agent", self._general)

        workflow.set_entry_point("router_node")
        workflow.add_conditional_edges(
            "router_node",
            lambda state: state["route"],
            {
                "risk_agent": "risk_agent",
                "deadline_agent": "deadline_agent",
                "blocker_agent": "blocker_agent",
                "team_agent": "team_agent",
                "general_agent": "general_agent",
            },
        )

        for node in ["risk_agent", "deadline_agent", "blocker_agent", "team_agent", "general_agent"]:
            workflow.add_edge(node, END)

        return workflow.compile()

    def _route(self, state: AgentState):
        return {"route": self.router.route(state["question"]) }

    def _risk(self, state: AgentState):
        return {"answer": self.risk_agent.run(state["question"], state["db"])}

    def _deadline(self, state: AgentState):
        return {"answer": self.deadline_agent.run(state["question"], state["db"])}

    def _blocker(self, state: AgentState):
        return {"answer": self.blocker_agent.run(state["question"], state["db"])}

    def _team(self, state: AgentState):
        return {"answer": self.team_agent.run(state["question"], state["db"])}

    def _general(self, state: AgentState):
        return {"answer": self.general_agent.run(state["question"], state["db"])}

    def run(self, question: str, db: Session) -> tuple[str, str]:
        result = self.graph.invoke({"question": question, "db": db, "route": "", "answer": ""})
        return result["route"], result["answer"]
