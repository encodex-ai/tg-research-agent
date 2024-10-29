from app.models.agent import AgentStatus
from app.services.telegram.service import TelegramService
from telegram import Update
from telegram.ext import ContextTypes


async def cancel_command(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user_id: str = str(update.effective_user.id)
    user = telegram_service.user_service.get_user(user_id)
    agent_id = user.agent_id
    agent = telegram_service.agent_service.get(agent_id)

    if agent:
        if agent.status == AgentStatus.RUNNING:
            telegram_service.agent_service.update_field(
                agent_id, "status", AgentStatus.CANCELLED
            )
            await update.message.reply_text(
                f"Research task is being cancelled. It may take a moment to stop completely."
            )
        elif agent.status == AgentStatus.CANCELLED:
            await update.message.reply_text(
                f"Research task is already in the process of being cancelled."
            )
        else:
            await update.message.reply_text(
                f"No running research task found. Current status: {agent.status}"
            )
    else:
        await update.message.reply_text(f"No active research task found.")
