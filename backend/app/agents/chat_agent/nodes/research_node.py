from app.agents.llm_node import LLMNode
from termcolor import colored
from app.utils.helper_functions import get_content
import json
from app.agents.research_agent.state import (
    get_default_research_state,
    get_agent_graph_state,
)
from app.agents.chat_agent.state import get_chat_agent_state
import logging
from app.agents.research_agent.state import ResearchAgentState
from app.agents.research_agent.research_agent import ResearchAgent
from pydantic import Field
from app.agents.base_node_output import BaseNodeOutput
from app.services.agent_service import AgentService
from app.models.agent import AgentStatus
from app.agents.base_node_output import BaseNodeOutput


class ResearchOutput(BaseNodeOutput):
    research_result: str = Field(description="The research results")


class ResearchNode(LLMNode):
    name = "Research"

    async def ainvoke(self, state, send_message=None):
        extractor_response_value = get_content(
            get_chat_agent_state(state=state, state_key="extractor_latest")
        )

        research_question_value = get_content(extractor_response_value).get(
            "research_question"
        )
        chat_id = get_chat_agent_state(state=state, state_key="chat_id")

        research_graph = ResearchAgent()

        await send_message(
            chat_id, f"Starting research on the question: {research_question_value}"
        )

        initial_state = get_default_research_state(prompt=research_question_value)

        agent_service = AgentService()

        agent_id = get_chat_agent_state(state=state, state_key="agent_id")

        # update agent
        agent = agent_service.get(agent_id)
        if agent:
            agent_service.update_field(agent_id, "status", AgentStatus.RUNNING)
            agent_service.update_field(agent_id, "description", research_question_value)

        research_output = ""
        agent_id = get_chat_agent_state(state=state, state_key="agent_id")

        # TODO: Consolidate this with the handling in chat.py
        async for event in research_graph.async_stream(initial_state):
            event_node = list(event.keys())[0]
            research_state: ResearchAgentState = event[event_node]

            # Check if this agent has been cancelled
            if agent_service.get(agent_id).status == AgentStatus.CANCELLED:
                await send_message(chat_id, f"Research cancelled")
                break

            if event_node == "final_report":
                await send_message(chat_id, f"Beep boop, I'm done!")
                research_output = get_content(
                    get_agent_graph_state(
                        state=research_state, state_key="final_report_response"
                    )
                )["content"]
                break
            else:
                # Get the summary from the state if available
                response_name = f"{event_node}_response"
                response = research_state.get(response_name)[-1]
                content = get_content(response)
                if content and "summary" in content:
                    await send_message(chat_id, content["summary"])
                else:
                    response = f"Processing {event_node}..."
                    await send_message(chat_id, response)

        output = ResearchOutput(
            research_result=research_output,
            summary=f"🔬 Finished research on {research_question_value}",
        )

        self.update_state("researcher_response", output, is_pydantic=True)
        logging.info(colored(f"Research 🔬: {research_output}", "cyan"))
        return self.state
