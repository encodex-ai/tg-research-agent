from abc import abstractmethod
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from app.config import Config
from app.agents.base_node import BaseNode


class LLMNode(BaseNode):

    def __init__(
        self,
        state: dict,
    ):
        config = Config()
        self.model_name = config.MODEL_NAME
        self.server = config.LLM_TYPE
        self.temperature = config.TEMPERATURE
        self.model_endpoint = config.OLLAMA_API_URL
        self.max_tokens = config.MAX_TOKENS
        self.state = state
        common_params = {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if self.server == "openai":
            self.model = ChatOpenAI(**common_params, api_key=config.OPENAI_API_KEY)
        elif self.server == "anthropic":
            self.model = ChatAnthropic(
                **common_params, api_key=config.ANTHROPIC_API_KEY
            )
        elif self.server == "ollama":
            ollama_params = {"base_url": self.model_endpoint, **common_params}
            self.model = ChatOllama(**ollama_params)
        else:
            raise ValueError(f"Unsupported server type: {self.server}")

    def get_llm(self):
        return self.model

    @abstractmethod
    async def ainvoke(self, state: dict):
        pass
