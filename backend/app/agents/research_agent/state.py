from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages


# Define the state object for the agent graph
class ResearchAgentState(TypedDict):
    research_question: str
    planner_response: Annotated[list, add_messages]
    selector_response: Annotated[list, add_messages]
    reporter_response: Annotated[list, add_messages]
    reviewer_response: Annotated[list, add_messages]
    router_response: Annotated[list, add_messages]
    serper_response: Annotated[list, add_messages]
    scraper_response: Annotated[list, add_messages]
    final_report_response: str


# Define the default initial state
def get_default_research_state(prompt=""):
    return {
        "research_question": prompt,
        "planner_response": [],
        "selector_response": [],
        "reporter_response": [],
        "reviewer_response": [],
        "router_response": [],
        "serper_response": [],
        "scraper_response": [],
        "final_report_response": "",
    }


# Define the nodes in the agent graph
def get_agent_graph_state(state: ResearchAgentState, state_key: str):
    if "all" in state_key:
        key = state_key[:-4]  # example: planner_all -> planner

        if key + "_response" in state:
            return state[key + "_response"]
        else:
            return state[key]

    elif "latest" in state_key:  # example: serper_latest -> serper_response[-1]
        response_key = state_key[:-6] + "response"
        return state[response_key][-1] if state[response_key] else []
    elif state_key in state:
        return state[state_key]
    else:
        return []
