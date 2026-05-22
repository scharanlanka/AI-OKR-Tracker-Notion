from typing import TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from agents.read_agent import ReadAgent
from agents.router_agent import RouterAgent
from agents.write_agent import WriteAgent
from llm import AzureLLMClient


class AgentState(TypedDict):
    question: str
    route: str
    answer: str
    db: Session


class OKRGraph:
    """3-agent architecture: router -> read/write."""

    def __init__(self):
        llm_client = AzureLLMClient()
        self.router = RouterAgent(llm_client)
        self.read_agent = ReadAgent(llm_client)
        self.write_agent = WriteAgent(llm_client)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("router_node", self._route)
        workflow.add_node("read_agent", self._read)
        workflow.add_node("write_agent", self._write)

        workflow.set_entry_point("router_node")
        workflow.add_conditional_edges(
            "router_node",
            lambda state: state["route"],
            {
                "read_agent": "read_agent",
                "write_agent": "write_agent",
            },
        )

        workflow.add_edge("read_agent", END)
        workflow.add_edge("write_agent", END)

        return workflow.compile()

    def _route(self, state: AgentState):
        return {"route": self.router.route(state["question"])}

    def _read(self, state: AgentState):
        return {"answer": self.read_agent.run(state["question"], state["db"])}

    def _write(self, state: AgentState):
        return {"answer": self.write_agent.run(state["question"], state["db"])}

    def run(self, question: str, db: Session) -> tuple[str, str]:
        result = self.graph.invoke({"question": question, "db": db, "route": "", "answer": ""})
        return result["route"], result["answer"]
