from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from .routes import (
    start,
    cancel,
    status,
    help,
    chat,
)


class TelegramRouter:
    def __init__(self, telegram_service):
        self.telegram_service = telegram_service

    def register_handlers(self, application: Application):
        """Register all command and message handlers"""

        # Register command handlers
        application.add_handler(
            CommandHandler(
                "start",
                lambda update, context: start.start_command(
                    self.telegram_service, update, context
                ),
            )
        )
        application.add_handler(
            CommandHandler(
                "cancel",
                lambda update, context: cancel.cancel_command(
                    self.telegram_service, update, context
                ),
            )
        )
        application.add_handler(
            CommandHandler(
                "help",
                lambda update, context: help.help_command(
                    self.telegram_service, update, context
                ),
            )
        )
        application.add_handler(
            CommandHandler(
                "status",
                lambda update, context: status.status_command(
                    self.telegram_service, update, context
                ),
            )
        )

        # Register message handlers
        application.add_handler(
            CallbackQueryHandler(
                lambda update, context: chat.process_message_with_chat_agent(
                    self.telegram_service, update, context
                )
            )
        )
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                lambda update, context: chat.process_message_with_chat_agent(
                    self.telegram_service, update, context
                ),
            )
        )
