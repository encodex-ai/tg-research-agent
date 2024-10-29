import logging
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager


from app.config import Config
from app.database.mongodb import mongo_db
from app.routes.webhook import router as webhook_router
from app.services.telegram.service import TelegramService
from app.config import Config
from app.services.telegram.router import TelegramRouter

config = Config()


def configure_logging():
    log_level = logging.DEBUG if config.ENVIRONMENT == "development" else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",
    )
    logger = logging.getLogger("uvicorn")
    logger.setLevel(log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    telegram_token = config.TELEGRAM_BOT_TOKEN
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

    telegram_service = TelegramService(telegram_token)

    # Create and register the router before setup
    router = TelegramRouter(telegram_service)
    telegram_service.register_router(router)

    # Now setup the service
    await telegram_service.setup()
    app.state.telegram_service = telegram_service
    logging.info("Telegram service initialized successfully")

    yield

    # Shutdown
    await telegram_service.shutdown()
    logging.info("Application shutdown complete")


def create_app() -> FastAPI:
    logging.info("Creating FastAPI app...")

    # Add startup event for Telegram service initialization
    app = FastAPI(lifespan=lifespan)

    # Configure the app
    app.state.mongodb_atlas_uri = config.MONGODB_ATLAS_URI
    app.state.flask_env = config.ENVIRONMENT

    # Initialize the database
    mongo_db.init_app()

    # Configure logging
    configure_logging()

    # Include routers
    app.include_router(webhook_router)

    logging.info("FastAPI app setup complete.")
    return app


app = create_app()

if __name__ == "__main__":
    port = config.PORT

    # Replit-specific configuration
    if config.REPL_ID:
        host = "0.0.0.0"
        # Use Replit's provided URL for webhook
        repl_url = config.REPL_SLUG
        config.CLOUD_RUN_SERVICE_URL = f"https://{repl_url}.{config.REPL_OWNER}.repl.co"
    else:
        host = "127.0.0.1"

    app = create_app()
    uvicorn.run(app, host=host, port=port)
