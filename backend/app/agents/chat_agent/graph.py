import logging
from app.agents.chat_agent.chat_graph import build_chat_agent_graph

logger = logging.getLogger(__name__)

graph = build_chat_agent_graph()

__all__ = ["graph"]
