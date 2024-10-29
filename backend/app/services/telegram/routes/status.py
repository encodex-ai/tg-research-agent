from app.models.agent import AgentStatus
from telegram import Update
from telegram.ext import ContextTypes
from app.services.telegram.service import TelegramService


async def status_command(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = telegram_service.user_service.get_user(str(update.effective_user.id))
    agent = telegram_service.agent_service.get(user.agent_id)

    if not agent:
        await update.message.reply_text("There's no active research task.")
        return

    status_text = f"Research task status: {agent.status}\n"
    status_text += f"Task: {agent.name}\n"
    status_text += f"Description: {agent.description}\n"
    status_text += f"Current node: {agent.current_node or 'Not started'}\n"
    status_text += f"Last update: {agent.updated_at}"

    if agent.status == AgentStatus.ERROR:
        status_text += f"\nError: {agent.error}"

    await update.message.reply_text(status_text)
