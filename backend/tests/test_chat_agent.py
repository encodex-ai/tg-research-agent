import pytest
from unittest.mock import AsyncMock, patch
from app.agents.chat_agent.chat_agent import ChatAgent
from app.agents.chat_agent.state import get_default_chat_state


@pytest.mark.asyncio
async def test_chat_agent_simple_query():
    with patch("app.agents.chat_agent.chat_agent.build_chat_agent_graph") as mock_graph:
        mock_graph.return_value.ainvoke = AsyncMock(
            return_value={
                "finalizer_response": {"response": "Paris is the capital of France."}
            }
        )

        agent = ChatAgent()
        initial_state = get_default_chat_state(
            chat_id="test_chat", current_message="What is the capital of France?"
        )

        result = await agent.async_run(initial_state)

        assert result is not None
        assert isinstance(result, dict)
        assert "finalizer_response" in result
        assert "Paris" in result["finalizer_response"].get("response", "")


@pytest.mark.asyncio
async def test_chat_agent_complex_query():
    with patch("app.agents.chat_agent.chat_agent.build_chat_agent_graph") as mock_graph:
        mock_response = {
            "finalizer_response": {
                "response": """Photosynthesis is a process used by plants to convert light energy into chemical energy. 
                This process involves chlorophyll, sunlight, and carbon dioxide to produce glucose and oxygen."""
            }
        }
        mock_graph.return_value.ainvoke = AsyncMock(return_value=mock_response)

        agent = ChatAgent()
        initial_state = get_default_chat_state(
            chat_id="test_chat",
            current_message="Explain the process of photosynthesis in plants",
        )

        result = await agent.async_run(initial_state)

        assert result is not None
        assert isinstance(result, dict)
        assert "finalizer_response" in result
        response = result["finalizer_response"].get("response", "")
        assert "chlorophyll" in response.lower()
        assert "sunlight" in response.lower()
        assert "carbon dioxide" in response.lower()


@pytest.mark.asyncio
async def test_chat_agent_followup():
    with patch("app.agents.chat_agent.chat_agent.build_chat_agent_graph") as mock_graph:
        mock_responses = [
            {
                "finalizer_response": {
                    "response": "Neil Armstrong was the first person to walk on the moon."
                },
                "chat_history": [],  # Add this line to include chat history
            },
            {
                "finalizer_response": {"response": "The mission was Apollo 11."},
                "chat_history": [],  # Add this line to include chat history
            },
        ]
        mock_graph.return_value.ainvoke = AsyncMock(side_effect=mock_responses)

        agent = ChatAgent()
        initial_state = get_default_chat_state(
            chat_id="test_chat",
            current_message="Who was the first person to walk on the moon?",
        )

        result = await agent.async_run(initial_state)

        assert result is not None
        assert isinstance(result, dict)
        assert "finalizer_response" in result
        assert "chat_history" in result
        response = result["finalizer_response"].get("response", "")
        assert "Neil Armstrong" in response

        followup_state = get_default_chat_state(
            chat_id="test_chat",
            current_message="What was the name of the mission?",
            chat_history=result["chat_history"],
        )

        followup_result = await agent.async_run(followup_state)

        assert followup_result is not None
        assert isinstance(followup_result, dict)
        assert "finalizer_response" in followup_result
        followup_response = followup_result["finalizer_response"].get("response", "")
        assert "Apollo 11" in followup_response
