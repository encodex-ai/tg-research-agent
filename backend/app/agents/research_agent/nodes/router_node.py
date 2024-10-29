from enum import Enum
from pydantic import BaseModel, Field
from app.agents.llm_node import LLMNode
from app.utils.helper_functions import get_current_utc_datetime, get_content
from app.agents.research_agent.state import get_agent_graph_state
from termcolor import colored
from app.prompts.prompts import router_prompt_template
import logging
from app.agents.base_node_output import BaseNodeOutput


class AgentType(str, Enum):
    FINAL_REPORT = "final_report"
    PLANNER = "planner"
    REPORTER = "reporter"
    SELECTOR = "selector"


class RouterOutput(BaseNodeOutput):
    next_agent: AgentType = Field(
        description="The next agent to be called",
        examples=["final_report", "planner", "reporter", "selector"],
    )

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            self.summary = f"🔄 Routing to {self.next_agent.value} node"


class RouterNode(LLMNode):
    name = "Router"

    async def ainvoke(self, state):
        feedback_value = get_content(
            get_agent_graph_state(state=state, state_key="reviewer_latest")
        )

        router_prompt = router_prompt_template.format(
            feedback=feedback_value if feedback_value else "",
            datetime=get_current_utc_datetime(),
        )

        messages = [
            {"role": "system", "content": router_prompt},
            {
                "role": "user",
                "content": "Please provide your response in the given json format. Only respond with the 'next_agent' to be called.",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(RouterOutput)
        router_output: RouterOutput = await structured_llm.ainvoke(messages)

        self.update_state("router_response", router_output, is_pydantic=True)
        logging.info(colored(f"Router 🚦: {router_output}", "yellow"))

        return self.state
