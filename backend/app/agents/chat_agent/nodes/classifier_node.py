from app.agents.llm_node import LLMNode
from termcolor import colored
from app.prompts.prompts import classifier_prompt_template
from app.utils.helper_functions import format_chat_history, get_content
from app.agents.chat_agent.state import get_chat_agent_state
import logging
from pydantic import Field
from app.agents.base_node_output import BaseNodeOutput
from typing import Literal


class ClassifierOutput(BaseNodeOutput):
    function_name: Literal["help", "status", "cancel"] = Field(
        description="The function to call"
    )

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            self.summary = f"🏷️ Classified as {self.function_name} command"


class ClassifierNode(LLMNode):
    name = "Classifier"

    async def ainvoke(self, state):
        chat_history_value = get_content(
            get_chat_agent_state(state=state, state_key="chat_history")
        )
        current_message_value = get_content(
            get_chat_agent_state(state=state, state_key="current_message")
        )

        classifier_prompt = classifier_prompt_template.format(
            chat_history=format_chat_history(chat_history_value),
            current_message=current_message_value,
        )

        messages = [
            {"role": "system", "content": classifier_prompt},
            {
                "role": "user",
                "content": f"Classify this input: {current_message_value}",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(ClassifierOutput)
        classifier_output = await structured_llm.ainvoke(messages)

        self.update_state("classifier_response", classifier_output, is_pydantic=True)
        logging.info(colored(f"Classifier 🏷️: {classifier_output}", "yellow"))
        return self.state
