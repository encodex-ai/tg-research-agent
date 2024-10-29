from termcolor import colored
from app.agents.llm_node import LLMNode
from app.prompts.prompts import planner_prompt_template
from app.utils.helper_functions import get_current_utc_datetime, get_content
from app.agents.research_agent.state import get_agent_graph_state
from pydantic import BaseModel, Field
import logging
from app.agents.base_node_output import BaseNodeOutput


class PlannerOutput(BaseNodeOutput):
    search_term: str = Field(description="The most relevant search term to start with")
    overall_strategy: str = Field(
        description="The overall strategy to guide the search process"
    )
    additional_information: str = Field(
        description="Any additional information to guide the search including other search terms or filters"
    )

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            self.summary = f"📋 Planning to search for '{self.search_term}'"


class PlannerNode(LLMNode):
    name = "Planner"

    async def ainvoke(self, state):
        feedback_value = get_content(
            get_agent_graph_state(state=state, state_key="reviewer_latest")
        )

        planner_prompt = planner_prompt_template.format(
            feedback=feedback_value if feedback_value else "",
            datetime=get_current_utc_datetime(),
        )

        messages = [
            {"role": "system", "content": planner_prompt},
            {
                "role": "user",
                "content": f"research question: {state['research_question']}",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(PlannerOutput)
        planner_output: PlannerOutput = await structured_llm.ainvoke(messages)

        self.update_state("planner_response", planner_output, is_pydantic=True)
        logging.info(colored(f"Planner 👩🏿‍💻: {planner_output}", "cyan"))
        return self.state
