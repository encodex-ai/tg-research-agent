import pytest
from app.main import create_app
from app.database.mongodb import mongo_db
from mongomock import MongoClient
from app.agents.research_agent.research_graph import create_research_agent_graph
from app.services.telegram.service import TelegramService
import logging
from fastapi.testclient import TestClient
from datetime import datetime
from app.models.user import User
from app.models.agent import Agent, AgentStatus


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="function")
def mongodb():
    # Use MongoMock instead of real MongoDB
    mock_client = MongoClient()
    mock_db = mock_client.db
    mongo_db.client = mock_client
    mongo_db.db = mock_db
    return mongo_db


@pytest.fixture(scope="function")
def test_client(app):

    # Create TelegramService with mock services and a dummy token
    telegram_service = TelegramService(token="dummy_token")

    # Inject the mock TelegramService into the app
    app.state.telegram_service = telegram_service

    # Create a test client using the FastAPI application configured for testing
    with TestClient(app) as test_client:
        yield test_client  # this is where the testing happens!


@pytest.fixture(scope="function")
def init_database(mongodb):
    # Drop existing collections if they exist
    mongodb.db.drop_collection("users")
    mongodb.db.drop_collection("agents")

    # Create the collections
    mongodb.db.create_collection("users")
    mongodb.db.create_collection("agents")

    # Add some test data
    test_user = User(
        user_id="test_user",
        first_name="Test",
        last_name="User",
        successful_reports=0,
        last_request=datetime.now(),
    )
    mongodb.db.users.insert_one(test_user.to_dict())

    test_agent = Agent(
        agent_id="test_agent",
        user_id="test_user",
        name="Test Agent",
        description="A test research agent",
        status=AgentStatus.IDLE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mongodb.db.agents.insert_one(test_agent.to_dict())

    yield

    # Cleanup after test
    mongodb.db.drop_collection("users")
    mongodb.db.drop_collection("agents")
    print("Database cleaned up")


def research_agent_graph():
    return create_research_agent_graph()
