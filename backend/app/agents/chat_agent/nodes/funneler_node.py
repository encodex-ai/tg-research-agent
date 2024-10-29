import logging
from termcolor import colored
from app.agents.llm_node import LLMNode
from app.prompts.prompts import funneler_prompt_template
from app.utils.helper_functions import format_chat_history, get_content
from app.agents.chat_agent.state import get_chat_agent_state
import logging
from pydantic import BaseModel, Field
from app.agents.base_node_output import BaseNodeOutput


class FunnelerOutput(BaseNodeOutput):
    is_research_query: bool = Field(
        description="Whether the query is related to research"
    )

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            action = (
                "research query" if self.is_research_query else "command/conversation"
            )
            self.summary = f"🔍 Identified message as a {action}"


class FunnelerNode(LLMNode):
    name = "Funneler"

    async def ainvoke(self, state):
        chat_history_value = get_content(
            get_chat_agent_state(state=state, state_key="chat_history")
        )
        current_message_value = get_content(
            get_chat_agent_state(state=state, state_key="current_message")
        )

        funneler_prompt = funneler_prompt_template.format(
            chat_history=(
                format_chat_history(chat_history_value) if chat_history_value else ""
            ),
            current_message=current_message_value if current_message_value else "",
        )

        messages = [
            {"role": "system", "content": funneler_prompt},
            {
                "role": "user",
                "content": f"Determine if this is a research query: {current_message_value}",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(FunnelerOutput)
        funneler_output = await structured_llm.ainvoke(messages)

        self.update_state("funneler_response", funneler_output, is_pydantic=True)
        logging.info(f"Funneler 🧐: {funneler_output}")
        return self.state
