import logging
from time import perf_counter
from typing import TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from agents.read_agent import ReadAgent
from agents.router_agent import RouterAgent
from agents.write_agent import WriteAgent
from llm import AzureLLMClient

logger = logging.getLogger(__name__)


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
        start = perf_counter()
        route = self.router.route(state["question"])
        logger.info("agent_graph.router selected=%s duration=%.3fs", route, perf_counter() - start)
        return {"route": route}

    def _read(self, state: AgentState):
        start = perf_counter()
        logger.info("agent_graph.read_agent start")
        answer = self.read_agent.run(state["question"], state["db"])
        logger.info("agent_graph.read_agent done duration=%.3fs", perf_counter() - start)
        return {"answer": answer}

    def _write(self, state: AgentState):
        start = perf_counter()
        logger.info("agent_graph.write_agent start")
        answer = self.write_agent.run(state["question"], state["db"])
        logger.info("agent_graph.write_agent done duration=%.3fs", perf_counter() - start)
        return {"answer": answer}

    def run(self, question: str, db: Session) -> tuple[str, str]:
        total_start = perf_counter()
        logger.info("agent_graph.run start")
        result = self.graph.invoke({"question": question, "db": db, "route": "", "answer": ""})
        logger.info(
            "agent_graph.run done route=%s duration=%.3fs",
            result["route"],
            perf_counter() - total_start,
        )
        return result["route"], result["answer"]

    def route(self, question: str) -> str:
        return self.router.route(question)

    def stream(self, question: str, db: Session):
        total_start = perf_counter()
        logger.info("agent_graph.stream start")
        route_start = perf_counter()
        route = self.route(question)
        logger.info(
            "agent_graph.stream route=%s route_duration=%.3fs",
            route,
            perf_counter() - route_start,
        )
        if route == "read_agent":
            logger.info("agent_graph.stream delegated_to=read_agent total_setup=%.3fs", perf_counter() - total_start)
            return route, self.read_agent.run_stream(question, db)

        def _write_stream():
            write_start = perf_counter()
            text = self.write_agent.run(question, db)
            logger.info("agent_graph.stream write_agent completed duration=%.3fs", perf_counter() - write_start)
            for token in text.split(" "):
                yield token + " "

        logger.info("agent_graph.stream delegated_to=write_agent total_setup=%.3fs", perf_counter() - total_start)
        return route, _write_stream()
