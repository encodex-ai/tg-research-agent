from app.agents.llm_node import LLMNode
import requests
import json
from langchain_core.messages import ToolMessage
import logging
from app.config import Config
from app.agents.research_agent.state import get_agent_graph_state
from app.utils.helper_functions import get_content
from app.agents.base_node_output import BaseNodeOutput
from pydantic import Field


class WebSearchOutput(BaseNodeOutput):
    search_results: str = Field(description="The search results in JSON format")


class WebSearchNode(LLMNode):
    name = "WebSearch"

    def __init__(self, state: dict):
        super().__init__(state)
        config = Config()
        self.api_key = config.SERPER_API_KEY
        self.search_url = "https://google.serper.dev/search"

    async def ainvoke(self, state):
        query = get_content(
            get_agent_graph_state(state=state, state_key="planner_latest")
        )["search_term"]

        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {"q": query}
        logging.info(f"Searching for {query}")
        response = requests.post(self.search_url, headers=headers, json=payload)
        search_results = response.json()["organic"]

        # Format the search results as a message
        formatted_content = json.dumps(search_results, indent=2)

        output = WebSearchOutput(
            summary=f"🔍 Searched for '{query}' and found {len(search_results)} results",
            search_results=formatted_content,
        )

        self.update_state("serper_response", output, is_pydantic=True)
        logging.info(f"WebSearch 🔍: {output}")
        return self.state
