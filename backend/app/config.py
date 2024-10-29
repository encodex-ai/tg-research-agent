import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


class Config:
    # Environment
    DEBUG = False
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    PORT = int(os.getenv("PORT", 8080))

    # External Services
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    MONGODB_ATLAS_URI = os.getenv(
        "MONGODB_ATLAS_URI", "mongodb://localhost:27017/yourdb"
    )
    DB_NAME = os.getenv("DB_NAME", "your_database_name")

    # This is only necessary for the setting of the webhook
    CLOUD_RUN_SERVICE_URL = os.getenv("CLOUD_RUN_SERVICE_URL")

    # Web search settings
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")

    # LLM settings - you can add more LangChain supported models here
    LLM_TYPE = os.getenv("LLM_TYPE", "ollama")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://host.docker.internal:11434")

    # model settings
    MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS") or "4000")
    TEMPERATURE = float(os.getenv("TEMPERATURE") or "0.7")

    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Application specific settings

    # Replit settings
    REPL_ID = os.getenv("REPL_ID")
    REPL_SLUG = os.getenv("REPL_SLUG")
    REPL_OWNER = os.getenv("REPL_OWNER")
