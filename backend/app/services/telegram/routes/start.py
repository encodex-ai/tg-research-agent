import logging
from app.services.telegram.service import TelegramService
from .research import handle_start_research
from app.models.agent import AgentStatus


async def start_command(
    telegram_service: TelegramService,
    update,
    context,
) -> None:
    """
    Handle the /start command. Create a new user if they don't exist, welcome back existing users,
    and initiate research based on user input.
    """
    logging.info("start_chat handler called")
    research_question: str = update.message.text.replace("/start", "").strip()

    # Check if the user is already running research
    user = telegram_service.user_service.get_user(str(update.effective_user.id))
    agent = telegram_service.agent_service.get(user.agent_id)
    if agent.status == AgentStatus.RUNNING:
        await update.message.reply_text(
            "You are already running a research task or cancel it with /cancel"
        )
        return

    if research_question:
        try:
            await handle_start_research(
                telegram_service, update, context, research_question
            )
        except Exception as e:
            logging.error(f"Error in start_command: {str(e)}")
            await update.message.reply_text(
                "Sorry, an error occurred while processing your message."
            )
    else:
        await update.message.reply_text(
            "Please use /start <research_question> to start your research or /help for more information"
        )
