from app.agents.chat_agent.chat_graph import build_chat_agent_graph
import logging
import traceback
from typing import Dict, Any, AsyncGenerator


class ChatAgent:
    def __init__(self, send_message=None):
        self.graph = build_chat_agent_graph(send_message)
        self.send_message = send_message

    async def async_stream(
        self, initial_state: Dict[str, Any], recursion_limit: int = 40
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logging.info("Initial state %s", initial_state)
        limit = {"recursion_limit": recursion_limit}
        try:
            async for event in self.graph.astream(initial_state, limit):
                yield event

        except Exception as e:
            error_message = f"Error in chat agent: {str(e)}"
            logging.error(f"Error in async_stream: {traceback.format_exc()}")
            yield {"type": "event", "data": error_message}

    # Keep this method for backward compatibility if needed
    async def async_run(self, initial_state: Dict[str, Any], recursion_limit: int = 40):
        logging.info("Initial state %s", initial_state)
        limit = {"recursion_limit": recursion_limit}
        try:
            return await self.graph.ainvoke(initial_state, limit)

        except Exception as e:
            error_message = f"Error in chat agent: {str(e)}"
            logging.error("Error in async_run: %s", traceback.format_exc())
            return {"type": "event", "data": error_message}
