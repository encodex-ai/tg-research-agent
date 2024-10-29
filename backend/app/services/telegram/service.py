import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from app.services.user_service import UserService
from app.services.agent_service import AgentService
from app.services.chat_history_service import ChatHistoryService
from asyncio import Lock
from collections import defaultdict
from datetime import datetime
from app.models.agent import AgentStatus, Agent


class TelegramService:
    _instance = None
    MAX_SUCCESSFUL_REPORTS: int = 8

    def __new__(cls, token):
        if cls._instance is None:
            cls._instance = super(TelegramService, cls).__new__(cls)
            cls._instance.initialize(token)
        return cls._instance

    def initialize(self, token):
        logging.info("Setting up Telegram bot")
        self.token = token
        self.application = None
        self.is_setup = False
        self.user_service = UserService()
        self.agent_service = AgentService()
        self.chat_history_service = ChatHistoryService()
        self.user_locks = defaultdict(Lock)
        self.router = None

    def register_router(self, router):
        """Register the telegram router containing all command handlers"""
        self.router = router

    async def setup(self):
        if not self.is_setup:
            logging.info("Setting up Telegram bot handlers...")

            # Initialize the Telegram bot application
            self.application = Application.builder().token(self.token).build()

            if self.router:
                self.router.register_handlers(self.application)
            else:
                logging.error("No router registered. Bot will not handle any commands.")

            # Add error handler
            self.application.add_error_handler(self.error_handler)

            self.application.bot
            # Initialize and start the bot
            await self.application.initialize()
            await self.application.start()

            logging.info("Telegram bot is running.")
            self.is_setup = True

    async def shutdown(self):
        """Shutdown the bot application"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            logging.info("Telegram bot has been shut down.")

    async def run_middleware(self, update):
        e_user = update.effective_user
        user = self.user_service.get_user(str(e_user.id))

        if not user:
            # Create new user
            try:
                new_agent = self.agent_service.create_or_update(
                    Agent(
                        user_id=str(e_user.id),
                        name=f"{e_user.first_name}'s research agent",
                        description="",
                        status=AgentStatus.IDLE,
                    )
                )

                new_user = self.user_service.create_user(
                    {
                        "user_id": str(e_user.id),
                        "first_name": e_user.first_name,
                        "last_name": e_user.last_name,
                        "last_request": datetime.now(),
                        "agent_id": new_agent.agent_id,
                    }
                )
                logging.info(f"Created new user: {new_user.to_dict()}")
                logging.info(f"Created new agent: {new_agent.to_dict()}")
                await update.message.reply_text(
                    f"Hello {e_user.first_name}! I'm Jarvis! So nice to meet you!"
                )

            except ValueError as e:
                logging.error(f"Error creating user: {str(e)}")
                await update.message.reply_text(
                    "I'm sorry, there was an error creating your user profile. Please try again later."
                )
        else:
            # Send welcome back message if it's been over a day since the last request
            if user.last_request:
                time_since_last_request = datetime.now() - user.last_request
                if time_since_last_request.total_seconds() > 86400:
                    await update.message.reply_text(
                        f"Welcome back, {user.first_name}! Let's get rolling!"
                    )
                # Update agent
                agent = self.agent_service.get(user.agent_id)
                if agent:
                    self.agent_service.update_field(
                        agent.agent_id, "status", AgentStatus.IDLE
                    )

            self.user_service.update_user(
                user.user_id, {"last_request": datetime.now()}
            )

    async def send_message(self, chat_id, text, **kwargs):
        await self.application.bot.send_message(chat_id, text=text, **kwargs)

    async def error_handler(self, update, context):
        """
        Log errors caused by Updates.
        """
        logging.error(f"Update {update} caused error {context.error}")
