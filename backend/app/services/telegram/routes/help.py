from telegram import Update
from telegram.ext import ContextTypes
from app.services.telegram.service import TelegramService


async def help_command(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handle the /help command. Display available commands to the user.
    """
    help_text: str = (
        "Here are the commands you can use:\n"
        "/start <research_question> - Start a new research session\n"
        "/cancel - Cancel the current research task\n"
        "/status - Check the status of the current research task\n"
        "/help - Show this help message\n\n"
        "You can also simply type your research question to begin a new research session."
    )
    if update.message:
        await update.message.reply_text(help_text)
    else:
        await telegram_service.send_message(
            chat_id=update.effective_chat.id, text=help_text
        )
