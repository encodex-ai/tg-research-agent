import pytest
from datetime import datetime
from app.services.agent_service import AgentService
from app.models.agent import Agent, AgentStatus


@pytest.mark.usefixtures("init_database")
class TestAgentService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.agent_service = AgentService()

    def test_create_agent(self):
        agent_data = Agent(
            user_id="test_user",
            name="New Agent",
            description="Test agent description",
            status=AgentStatus.IDLE,
        )

        created_agent = self.agent_service.create_or_update(agent_data)
        assert created_agent is not None
        assert created_agent.agent_id is not None
        assert created_agent.name == "New Agent"
        assert created_agent.description == "Test agent description"
        assert created_agent.status == AgentStatus.IDLE
        assert isinstance(created_agent.created_at, datetime)
        assert isinstance(created_agent.updated_at, datetime)

    def test_get_agent(self):
        # First create an agent
        agent_data = Agent(
            user_id="test_user",
            name="Get Test Agent",
            description="Test retrieval",
            status=AgentStatus.IDLE,
        )
        created_agent = self.agent_service.create_or_update(agent_data)

        # Then retrieve it
        retrieved_agent = self.agent_service.get(created_agent.agent_id)
        assert retrieved_agent is not None
        assert retrieved_agent.agent_id == created_agent.agent_id
        assert retrieved_agent.name == "Get Test Agent"

    def test_update_agent(self):
        # First create an agent
        agent_data = Agent(
            user_id="test_user",
            name="Update Test Agent",
            description="Test update",
            status=AgentStatus.IDLE,
        )
        created_agent = self.agent_service.create_or_update(agent_data)

        # Update the agent
        created_agent.name = "Updated Agent"
        updated_agent = self.agent_service.create_or_update(created_agent)
        assert updated_agent.name == "Updated Agent"
        assert updated_agent.agent_id == created_agent.agent_id

    def test_delete_agent(self):
        # First create an agent
        agent_data = Agent(
            user_id="test_user",
            name="Delete Test Agent",
            description="Test deletion",
            status=AgentStatus.IDLE,
        )
        created_agent = self.agent_service.create_or_update(agent_data)

        # Delete the agent
        self.agent_service.delete(created_agent.agent_id)

        # Verify it's deleted
        retrieved_agent = self.agent_service.get(created_agent.agent_id)
        assert retrieved_agent is None

    def test_list_agents(self):
        # Create multiple agents
        agent_data1 = Agent(
            user_id="test_user",
            name="List Test Agent 1",
            description="Test listing 1",
            status=AgentStatus.IDLE,
        )
        agent_data2 = Agent(
            user_id="test_user",
            name="List Test Agent 2",
            description="Test listing 2",
            status=AgentStatus.RUNNING,
        )
        self.agent_service.create_or_update(agent_data1)
        self.agent_service.create_or_update(agent_data2)

        # List all agents
        agents = self.agent_service.list()
        assert len(agents) >= 2

        # List with filter
        running_agents = self.agent_service.list({"status": AgentStatus.RUNNING})
        assert len(running_agents) >= 1
        assert all(agent.status == AgentStatus.RUNNING for agent in running_agents)

    def test_update_field(self):
        # First create an agent
        agent_data = Agent(
            user_id="test_user",
            name="Field Update Test Agent",
            description="Test field update",
            status=AgentStatus.IDLE,
        )
        created_agent = self.agent_service.create_or_update(agent_data)

        # Update a specific field
        updated_agent = self.agent_service.update_field(
            created_agent.agent_id, "status", AgentStatus.RUNNING
        )
        assert updated_agent is not None
        assert updated_agent.status == AgentStatus.RUNNING

    def test_update_nonexistent_agent(self):
        result = self.agent_service.update_field(
            "nonexistent_id", "status", AgentStatus.RUNNING
        )
        assert result is None


if __name__ == "__main__":
    pytest.main()
