from app.agents.llm_node import LLMNode
from app.prompts.prompts import reporter_prompt_template
from app.utils.helper_functions import get_current_utc_datetime, get_content
from app.agents.research_agent.state import get_agent_graph_state
from termcolor import colored
import logging
from pydantic import Field
from app.agents.base_node_output import BaseNodeOutput
import json


class ReporterOutput(BaseNodeOutput):
    content: str = Field(description="The generated report content")


class ReporterNode(LLMNode):
    name = "Reporter"

    async def ainvoke(self, state):
        feedback_value = get_content(
            get_agent_graph_state(state=state, state_key="reviewer_latest")
        )
        previous_reports_value = get_content(
            get_agent_graph_state(state=state, state_key="reporter_all")
        )
        research_value = get_content(
            get_agent_graph_state(state=state, state_key="scraper_latest")
        )

        research_value = get_content(research_value).get("results")
        logging.info(f"Reporter 📝: Research value: {research_value}")

        reporter_prompt = reporter_prompt_template.format(
            feedback=feedback_value if feedback_value else "",
            previous_reports=previous_reports_value if previous_reports_value else "",
            datetime=get_current_utc_datetime(),
            research_links=(
                "\n".join([link["source"] for link in get_content(research_value)])
                if research_value
                else ""
            ),
            research_content=research_value if research_value else "",
        )

        messages = [
            {"role": "system", "content": reporter_prompt},
            {
                "role": "user",
                "content": f"research question: {state['research_question']}",
            },
        ]

        llm = self.get_llm()
        ai_msg = await llm.ainvoke(messages)
        response = ai_msg.content

        output = ReporterOutput(
            content=response, summary="📝 Generated research report"
        )

        self.update_state("reporter_response", output, is_pydantic=True)
        logging.info(colored(f"Reporter 👨‍💻: {response}", "yellow"))
        return self.state
