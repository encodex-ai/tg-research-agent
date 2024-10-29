from app.agents.llm_node import LLMNode
from termcolor import colored
from app.prompts.prompts import questioner_prompt_template
from app.utils.helper_functions import format_chat_history, get_content
from app.agents.chat_agent.state import get_chat_agent_state
import logging
from pydantic import Field
from app.agents.base_node_output import BaseNodeOutput


class QuestionerOutput(BaseNodeOutput):
    clarifying_question: str = Field(
        description="The question to ask for clarification"
    )

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            self.summary = f"❓ Asking for clarification: '{self.clarifying_question}'"


class QuestionerNode(LLMNode):
    name = "Questioner"

    async def ainvoke(self, state):
        chat_history_value = get_content(
            get_chat_agent_state(state=state, state_key="chat_history")
        )
        current_message_value = get_content(
            get_chat_agent_state(state=state, state_key="current_message")
        )
        research_question_value = get_content(
            get_chat_agent_state(state=state, state_key="extractor_latest")
        )

        questioner_prompt = questioner_prompt_template.format(
            chat_history=(
                format_chat_history(chat_history_value) if chat_history_value else ""
            ),
            current_message=current_message_value if current_message_value else "",
            research_question=(
                research_question_value if research_question_value else ""
            ),
        )

        messages = [
            {"role": "system", "content": questioner_prompt},
            {
                "role": "user",
                "content": "Generate a clarifying question for the research.",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(QuestionerOutput)
        questioner_output = await structured_llm.ainvoke(messages)

        self.update_state("questioner_response", questioner_output, is_pydantic=True)
        logging.info(colored(f"Questioner ❓: {questioner_output}", "magenta"))
        return self.state
