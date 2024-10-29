from app.agents.llm_node import LLMNode
from termcolor import colored
from app.utils.helper_functions import get_content
from app.agents.chat_agent.state import get_chat_agent_state
import logging
from pydantic import BaseModel, Field
from typing import Optional


class FinalizerOutput(BaseModel):
    clarifying_question: Optional[str] = Field(
        default=None, description="The clarifying question if needed"
    )
    final_report: Optional[str] = Field(
        default=None, description="The final research report"
    )
    function_name: Optional[str] = Field(
        default=None, description="The function to call if any"
    )


class FinalizerNode(LLMNode):
    name = "Finalizer"

    async def ainvoke(self, state):
        questioner_response_value = get_content(
            get_chat_agent_state(state=state, state_key="questioner_latest")
        )
        research_response_value = get_content(
            get_chat_agent_state(state=state, state_key="researcher_latest")
        )
        classifier_response_value = get_content(
            get_chat_agent_state(state=state, state_key="classifier_latest")
        )

        clarifying_question = ""
        final_report = ""
        function_name = ""

        if questioner_response_value is not None:
            clarifying_question = get_content(questioner_response_value).get(
                "clarifying_question"
            )

        if research_response_value is not None:
            final_report = get_content(research_response_value).get("research_result")

        if classifier_response_value is not None:
            function_name = get_content(classifier_response_value).get("function_name")

        finalizer_output = FinalizerOutput(
            clarifying_question=clarifying_question,
            final_report=final_report,
            function_name=function_name,
        )

        self.update_state("finalizer_response", finalizer_output, is_pydantic=True)
        logging.info(colored(f"Finalizer 🏁: {finalizer_output}", "green"))
        return self.state
