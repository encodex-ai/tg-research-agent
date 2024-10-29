from langgraph.graph import StateGraph, END
from langgraph.pregel import RetryPolicy
import logging
from enum import Enum
from app.utils.helper_functions import get_content
from app.agents.chat_agent.nodes.funneler_node import FunnelerNode
from app.agents.chat_agent.nodes.extractor_node import ExtractorNode
from app.agents.chat_agent.nodes.clarifier_node import ClarifierNode
from app.agents.chat_agent.nodes.questioner_node import QuestionerNode
from app.agents.chat_agent.nodes.classifier_node import ClassifierNode
from app.agents.chat_agent.nodes.research_node import ResearchNode
from app.agents.chat_agent.nodes.finalizer_node import FinalizerNode
from app.agents.chat_agent.state import ChatAgentState, get_chat_agent_state


# Nodes Enum
class NodeName(str, Enum):
    FUNNELER = "funneler"
    EXTRACTOR = "extractor"
    CLARIFIER = "clarifier"
    QUESTIONER = "questioner"
    RESEARCHER = "researcher"
    CLASSIFIER = "classifier"
    FINALIZER = "finalizer"


# Conditional routing functions
def funneler_router(state) -> str:
    """Route based on whether the query is research-related"""
    is_research = get_content(
        get_chat_agent_state(state=state, state_key="funneler_latest")
    ).get("is_research_query")
    return NodeName.EXTRACTOR if is_research else NodeName.CLASSIFIER


def clarifier_router(state) -> str:
    """Route based on whether we have enough information"""
    has_enough_info = get_content(
        get_chat_agent_state(state=state, state_key="clarifier_latest")
    ).get("has_enough_info")
    return NodeName.RESEARCHER if has_enough_info else NodeName.QUESTIONER


def questioner_router(state) -> str:
    """Route based on number of clarification attempts"""
    chat_history = get_chat_agent_state(state=state, state_key="chat_history")
    clarification_count = len(
        [
            m
            for m in chat_history
            if m.role == "assistant" and m.additional_kwargs.get("is_clarification")
        ]
    )
    return NodeName.RESEARCHER if clarification_count >= 3 else NodeName.FINALIZER


def create_chat_agent_graph(send_message=None) -> StateGraph:
    graph = StateGraph(ChatAgentState)
    retry_policy = RetryPolicy(max_attempts=5)

    # Node wrapper functions
    async def ainvoke_funneler(state):
        return await FunnelerNode(state).ainvoke(state)

    async def ainvoke_extractor(state):
        return await ExtractorNode(state).ainvoke(state)

    async def ainvoke_clarifier(state):
        return await ClarifierNode(state).ainvoke(state)

    async def ainvoke_questioner(state):
        return await QuestionerNode(state).ainvoke(state)

    # We need to pass the send_message function to the researcher node so it can update the user
    async def ainvoke_researcher(state):
        return await ResearchNode(state).ainvoke(state, send_message=send_message)

    async def ainvoke_classifier(state):
        return await ClassifierNode(state).ainvoke(state)

    async def ainvoke_finalizer(state):
        return await FinalizerNode(state).ainvoke(state)

    # Add nodes
    graph.add_node(
        NodeName.FUNNELER,
        ainvoke_funneler,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.EXTRACTOR,
        ainvoke_extractor,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.CLARIFIER,
        ainvoke_clarifier,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.QUESTIONER,
        ainvoke_questioner,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.RESEARCHER,
        ainvoke_researcher,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.CLASSIFIER,
        ainvoke_classifier,
        retry=retry_policy,
    )

    graph.add_node(
        NodeName.FINALIZER,
        ainvoke_finalizer,
        retry=retry_policy,
    )

    # Set up the graph flow
    graph.set_entry_point(NodeName.FUNNELER)
    graph.add_conditional_edges(
        NodeName.FUNNELER,
        funneler_router,
        {
            NodeName.EXTRACTOR: NodeName.EXTRACTOR,
            NodeName.CLASSIFIER: NodeName.CLASSIFIER,
        },
    )
    graph.add_edge(NodeName.EXTRACTOR, NodeName.CLARIFIER)
    graph.add_conditional_edges(
        NodeName.CLARIFIER,
        clarifier_router,
        {
            NodeName.RESEARCHER: NodeName.RESEARCHER,
            NodeName.QUESTIONER: NodeName.QUESTIONER,
        },
    )
    graph.add_conditional_edges(
        NodeName.QUESTIONER,
        questioner_router,
        {
            NodeName.RESEARCHER: NodeName.RESEARCHER,
            NodeName.FINALIZER: NodeName.FINALIZER,
        },
    )
    graph.add_edge(NodeName.RESEARCHER, NodeName.FINALIZER)
    graph.add_edge(NodeName.CLASSIFIER, NodeName.FINALIZER)
    graph.add_edge(NodeName.FINALIZER, END)

    return graph


def build_chat_agent_graph(send_message=None):
    graph = create_chat_agent_graph(send_message)
    graph.name = "ChatAgent"
    return graph.compile()
