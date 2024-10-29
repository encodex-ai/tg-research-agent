from app.agents.llm_node import LLMNode
from app.utils.helper_functions import get_content
from app.agents.research_agent.state import get_agent_graph_state
from termcolor import colored
import logging


class FinalReportNode(LLMNode):
    name = "FinalReport"

    async def ainvoke(self, state):
        final_response_value = get_content(
            get_agent_graph_state(state=state, state_key="reporter_latest")
        )

        self.update_state("final_report_response", final_response_value)
        logging.info(colored(f"Final Report 📝: {final_response_value}", "blue"))
        return self.state
