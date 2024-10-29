from app.agents.llm_node import LLMNode
from termcolor import colored
from app.prompts.prompts import clarifier_prompt_template
from app.utils.helper_functions import format_chat_history, get_content
from app.agents.chat_agent.state import get_chat_agent_state
import logging
from pydantic import Field
from app.agents.base_node_output import BaseNodeOutput
from typing import List
from langchain_core.messages import ChatMessage


class ClarifierOutput(BaseNodeOutput):
    has_enough_info: bool = Field(description="Whether there is sufficient information")
    reasoning: str = Field(
        description="Explanation if clarification is needed", default=""
    )

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            status = (
                "✅ Have enough information"
                if self.has_enough_info
                else "❓ Need clarification"
            )
            self.summary = f"🤔 {status}"


class ClarifierNode(LLMNode):
    name = "Clarifier"

    async def ainvoke(self, state):
        chat_history_value: List[ChatMessage] = get_content(
            get_chat_agent_state(state=state, state_key="chat_history")
        )
        current_message_value: str = get_content(
            get_chat_agent_state(state=state, state_key="current_message")
        )
        extractor_latest_value = get_content(
            get_chat_agent_state(state=state, state_key="extractor_latest")
        )

        research_question = extractor_latest_value["research_question"]

        clarifier_prompt = clarifier_prompt_template.format(
            chat_history=format_chat_history(chat_history_value),
            current_message=current_message_value,
            research_question=research_question,
        )

        messages = [
            {"role": "system", "content": clarifier_prompt},
            {
                "role": "user",
                "content": "Determine if we have enough information to start research.",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(ClarifierOutput)
        clarifier_output = await structured_llm.ainvoke(messages)

        self.update_state("clarifier_response", clarifier_output, is_pydantic=True)
        logging.info(colored(f"Clarifier 🔍: {clarifier_output}", "blue"))
        return self.state
