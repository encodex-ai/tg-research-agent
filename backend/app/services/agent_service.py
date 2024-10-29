from bson import ObjectId
from typing import Any, Dict, List, Optional

from app.database.mongodb import mongo_db
from app.models.agent import Agent, AgentStatus


class AgentService:
    def __init__(self):
        self.collection = "agents"

    def create_or_update(self, agent: Agent) -> Agent:
        if not agent.agent_id:
            agent.agent_id = str(ObjectId())
            mongo_db.insert_one(self.collection, agent.to_dict())
        else:
            mongo_db.update_one(
                self.collection,
                {"agent_id": agent.agent_id},
                {"$set": agent.to_dict(), "$currentDate": {"updated_at": True}},
            )
        return agent

    def get(self, agent_id: str) -> Optional[Agent]:
        agent_data = mongo_db.find_one(self.collection, {"agent_id": agent_id})
        return Agent.from_dict(agent_data) if agent_data else None

    def delete(self, agent_id: str) -> None:
        mongo_db.delete_one(self.collection, {"agent_id": agent_id})

    def list(self, filter_dict: Dict[str, Any] = None) -> List[Agent]:
        agents = mongo_db.find(self.collection, filter_dict or {})
        return [Agent.from_dict(agent) for agent in agents]

    def update_field(self, agent_id: str, field: str, value: Any) -> Optional[Agent]:
        update_result = mongo_db.update_one(
            self.collection,
            {"agent_id": agent_id},
            {"$set": {field: value}, "$currentDate": {"updated_at": True}},
        )
        return self.get(agent_id) if update_result.modified_count > 0 else None

    def get_active_agents_for_user(self, user_id: str) -> List[Agent]:
        """Get all active research agents for a user."""
        return [
            agent
            for agent in self.get_agents_for_user(user_id)
            if agent.status == AgentStatus.RUNNING
        ]

    def get_agents_for_user(self, user_id: str) -> List[Agent]:
        """Get all agents for a user."""
        agents = mongo_db.find(self.collection, {"user_id": user_id})
        return [Agent.from_dict(agent) for agent in agents]
