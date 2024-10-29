from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langchain_core.messages import ChatMessage


class ChatAgentState(TypedDict):
    chat_history: Annotated[List[ChatMessage], add_messages]
    chat_id: str
    agent_id: str
    current_message: str
    # Node responses
    funneler_response: Annotated[list, add_messages]
    extractor_response: Annotated[list, add_messages]
    clarifier_response: Annotated[list, add_messages]
    classifier_response: Annotated[list, add_messages]
    questioner_response: Annotated[list, add_messages]
    researcher_response: Annotated[list, add_messages]
    finalizer_response: dict


def get_default_chat_state(
    chat_id: str = "",
    current_message: str = "",
    chat_history: list = [],
    agent_id: str = "",
) -> ChatAgentState:
    return {
        "chat_history": chat_history,
        "chat_id": chat_id,
        "agent_id": agent_id,
        "current_message": current_message,
        "funneler_response": [],
        "extractor_response": [],
        "clarifier_response": [],
        "classifier_response": [],
        "questioner_response": [],
        "researcher_response": [],
        "finalizer_response": {},
    }


def get_chat_agent_state(state: ChatAgentState, state_key: str):
    if "all" in state_key:
        key = state_key[:-4]  # example: funneler_all -> funneler
        if key + "_response" in state:
            return state[key + "_response"]
        else:
            return state[key]  #
    elif "latest" in state_key:  # example: serper_latest -> serper_response[-1]
        response_key = state_key[:-6] + "response"
        return state[response_key][-1] if state[response_key] else []
    elif state_key in state:
        return state[state_key]
    else:
        return []
