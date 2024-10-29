from langgraph.graph import StateGraph, END
from langgraph.pregel import RetryPolicy
import logging
from enum import Enum

from app.utils.helper_functions import get_content
from app.agents.research_agent.nodes.web_scraper_node import WebScraperNode
from app.agents.research_agent.nodes.web_search_node import WebSearchNode
from app.agents.research_agent.nodes.planner_node import PlannerNode
from app.agents.research_agent.nodes.selector_node import SelectorNode
from app.agents.research_agent.nodes.reporter_node import ReporterNode
from app.agents.research_agent.nodes.reviewer_node import ReviewerNode
from app.agents.research_agent.nodes.router_node import RouterNode, AgentType
from app.agents.research_agent.nodes.final_report_node import FinalReportNode

from app.agents.research_agent.state import (
    ResearchAgentState,
    get_agent_graph_state,
)

logging.basicConfig(level=logging.INFO)


# Node wrapper functions
async def ainvoke_planner(state):
    return await PlannerNode(state).ainvoke(state)


async def ainvoke_selector(state):
    return await SelectorNode(state).ainvoke(state)


async def ainvoke_reporter(state):
    return await ReporterNode(state).ainvoke(state)


async def ainvoke_reviewer(state):
    return await ReviewerNode(state).ainvoke(state)


async def ainvoke_router(state):
    return await RouterNode(state).ainvoke(state)


async def ainvoke_final_report(state):
    return await FinalReportNode(state).ainvoke(state)


# Tool wrapper functions
async def ainvoke_web_search(state):
    return await WebSearchNode(state).ainvoke(state)


async def ainvoke_web_scraper(state):
    return await WebScraperNode(state).ainvoke(state)


class NodeName(str, Enum):
    PLANNER = "planner"
    SELECTOR = "selector"
    REPORTER = "reporter"
    REVIEWER = "reviewer"
    ROUTER = "router"
    SERPER = "serper"
    SCRAPER = "scraper"
    FINAL_REPORT = "final_report"


def create_research_agent_graph() -> StateGraph:
    graph = StateGraph(ResearchAgentState)
    retry_policy = RetryPolicy(max_attempts=5)

    # Add nodes
    graph.add_node(
        NodeName.PLANNER,
        ainvoke_planner,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.SELECTOR,
        ainvoke_selector,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.REPORTER,
        ainvoke_reporter,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.REVIEWER,
        ainvoke_reviewer,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.ROUTER,
        ainvoke_router,
        retry=retry_policy,
    )

    # Tool nodes
    graph.add_node(
        NodeName.SERPER,
        ainvoke_web_search,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.SCRAPER,
        ainvoke_web_scraper,
        retry=retry_policy,
    )

    # Final Report Node
    graph.add_node(
        NodeName.FINAL_REPORT,
        ainvoke_final_report,
        retry=retry_policy,
    )

    # Set entry point and edges
    graph.set_entry_point(NodeName.PLANNER)
    graph.add_edge(NodeName.PLANNER, NodeName.SERPER)
    graph.add_edge(NodeName.SERPER, NodeName.SELECTOR)
    graph.add_edge(NodeName.SELECTOR, NodeName.SCRAPER)
    graph.add_edge(NodeName.SCRAPER, NodeName.REPORTER)
    graph.add_edge(NodeName.REPORTER, NodeName.REVIEWER)
    graph.add_edge(NodeName.REVIEWER, NodeName.ROUTER)

    # Add conditional edges for router
    graph.add_conditional_edges(
        NodeName.ROUTER,
        router_condition,
        {
            AgentType.FINAL_REPORT: NodeName.FINAL_REPORT,
            AgentType.PLANNER: NodeName.PLANNER,
            AgentType.REPORTER: NodeName.REPORTER,
            AgentType.SELECTOR: NodeName.SELECTOR,
        },
    )

    graph.add_edge(NodeName.FINAL_REPORT, END)

    return graph


def router_condition(state: ResearchAgentState) -> AgentType:
    """
    Determines the next node based on router output.
    Returns the AgentType enum value directly.
    """
    router_value = get_agent_graph_state(state=state, state_key="router_latest")
    if not router_value:
        raise ValueError("No router value found in state")

    content = get_content(router_value)
    if isinstance(content, dict):
        next_agent = content.get("next_agent")
        if not next_agent:
            raise ValueError("No next_agent found in router output")
        return AgentType(next_agent)
    else:
        raise ValueError(f"Unexpected router output format: {content}")


def build_research_agent_graph():
    graph = create_research_agent_graph()
    graph.name = "ResearchAgent"
    return graph.compile()
