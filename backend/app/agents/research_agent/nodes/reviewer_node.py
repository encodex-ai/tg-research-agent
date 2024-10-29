from app.prompts.prompts import reviewer_prompt_template
from pydantic import BaseModel, Field, field_validator
from app.agents.llm_node import LLMNode
from app.utils.helper_functions import get_current_utc_datetime, get_content
from app.agents.research_agent.state import get_agent_graph_state
from termcolor import colored
import logging
from app.agents.base_node_output import BaseNodeOutput


class ReviewerOutput(BaseNodeOutput):
    feedback: str = Field(description="Detailed feedback explaining the review")
    comprehensive: bool = Field(description="Whether the response is comprehensive")
    citations_provided: bool = Field(description="Whether citations are provided")
    pass_review: bool = Field(description="Whether the response passes review")

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            status = "✅ Passed" if self.pass_review else "❌ Needs improvement"
            self.summary = f"📋 Review complete - {status}"


class ReviewerNode(LLMNode):
    name = "Reviewer"

    async def ainvoke(self, state):
        reporter_value = get_content(
            get_agent_graph_state(state=state, state_key="reporter_latest")
        )
        feedback_value = get_content(
            get_agent_graph_state(state=state, state_key="reviewer_all")
        )

        reviewer_prompt = reviewer_prompt_template.format(
            reporter=reporter_value["content"] if reporter_value else "",
            feedback=feedback_value if feedback_value else "",
            datetime=get_current_utc_datetime(),
            research_question=state["research_question"],
        )

        messages = [
            {"role": "system", "content": reviewer_prompt},
            {
                "role": "user",
                "content": "Evaluate the response and provide detailed feedback in the specified JSON format.",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(ReviewerOutput)
        reviewer_output: ReviewerOutput = await structured_llm.ainvoke(messages)

        self.update_state("reviewer_response", reviewer_output, is_pydantic=True)
        logging.info(colored(f"Reviewer 👩🏽‍⚖️: {reviewer_output}", "magenta"))
        return self.state
