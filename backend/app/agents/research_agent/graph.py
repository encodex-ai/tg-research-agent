import logging
from app.agents.research_agent.research_graph import build_research_agent_graph

logger = logging.getLogger(__name__)

graph = build_research_agent_graph()

__all__ = ["graph"]
