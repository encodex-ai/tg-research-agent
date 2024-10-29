import logging
from termcolor import colored
from pydantic import Field
from app.agents.llm_node import LLMNode
from app.prompts.prompts import selector_prompt_template
from app.utils.helper_functions import get_current_utc_datetime, get_content
from app.agents.research_agent.state import get_agent_graph_state
from app.agents.base_node_output import BaseNodeOutput


class SelectorOutput(BaseNodeOutput):
    selected_urls: str = Field(
        description="List of 2-4 selected urls, separated by commas"
    )

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            urls = self.selected_urls.split(", ")
            self.summary = f"🎯 Selected {len(urls)} relevant sources to analyze"


class SelectorNode(LLMNode):
    name = "Selector"

    async def ainvoke(self, state):
        feedback_value = get_content(
            get_agent_graph_state(state=state, state_key="reviewer_latest")
        )
        previous_selections_value = get_content(
            get_agent_graph_state(state=state, state_key="selector_all")
        )
        serp_value = get_content(
            get_agent_graph_state(state=state, state_key="serper_latest")
        )

        selector_prompt = selector_prompt_template.format(
            feedback=feedback_value if feedback_value else "",
            previous_selections=(
                previous_selections_value if previous_selections_value else ""
            ),
            serp=serp_value if serp_value else "",
            datetime=get_current_utc_datetime(),
            research_question=state["research_question"],
        )

        messages = [
            {"role": "system", "content": selector_prompt},
            {
                "role": "user",
                "content": "Please select 2-3 most relevant links from the search engine results page. Provide each link's URL in the format specified in the prompt. ONLY RETURN THE URLS IN THE JSON FORMAT, NOTHING ELSE.",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(SelectorOutput)
        selector_output = await structured_llm.ainvoke(messages)
        selector_output.selected_urls = selector_output.selected_urls.split(", ")

        self.update_state("selector_response", selector_output, is_pydantic=True)
        logging.info(colored(f"Selector 🧑🏼‍💻: {selector_output}", "green"))
        return self.state
