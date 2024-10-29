from app.agents.llm_node import LLMNode
from termcolor import colored
from app.prompts.prompts import extractor_prompt_template
from app.utils.helper_functions import format_chat_history, get_content
from app.agents.chat_agent.state import get_chat_agent_state
import logging
from pydantic import Field
from app.agents.base_node_output import BaseNodeOutput


class ExtractorOutput(BaseNodeOutput):
    research_question: str = Field(description="The extracted research question")

    def __init__(self, **data):
        super().__init__(**data)
        if "summary" not in data:
            self.summary = f"📝 Extracted question: '{self.research_question}'"


class ExtractorNode(LLMNode):
    name = "Extractor"

    async def ainvoke(self, state):
        chat_history_value = get_content(
            get_chat_agent_state(state=state, state_key="chat_history")
        )
        current_message_value = get_content(
            get_chat_agent_state(state=state, state_key="current_message")
        )
        previous_extractions = get_content(
            get_chat_agent_state(state=state, state_key="extractor_all")
        )

        previous_extractions = (
            [get_content(resp).research_question for resp in previous_extractions]
            if previous_extractions
            else []
        )
        previous_extractions_str = "\n".join(f"- {q}" for q in previous_extractions)

        extractor_prompt = extractor_prompt_template.format(
            chat_history=(
                format_chat_history(chat_history_value) if chat_history_value else ""
            ),
            current_message=current_message_value if current_message_value else "",
            previous_extractions=previous_extractions_str,
        )

        messages = [
            {"role": "system", "content": extractor_prompt},
            {
                "role": "user",
                "content": "Extract the research question from the conversation, considering the previous research questions.",
            },
        ]

        llm = self.get_llm()
        structured_llm = llm.with_structured_output(ExtractorOutput)
        extractor_output = await structured_llm.ainvoke(messages)

        self.update_state("extractor_response", extractor_output, is_pydantic=True)
        logging.info(colored(f"Extractor 📥: {extractor_output}", "green"))
        return self.state
