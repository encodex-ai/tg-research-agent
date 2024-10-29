import logging
from typing import Dict, Any, Optional, List
from app.utils.helper_functions import get_content
from telegram import Update
from telegram.ext import ContextTypes
from app.models.agent import AgentStatus, Agent
from app.agents.research_agent.research_agent import ResearchAgent
from app.agents.research_agent.state import get_default_research_state
from app.services.telegram.service import TelegramService


async def handle_start_research(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    research_question: Optional[str] = None,
) -> None:

    user_id: str = str(update.effective_user.id)

    if not research_question:
        await update.message.reply_text(
            "Please provide a research question. For example: /start what is quantum computing?"
        )
        return

    # Get all active agents for this user
    active_agents: List[Agent] = (
        telegram_service.agent_service.get_active_agents_for_user(user_id)
    )

    if active_agents:
        await update.message.reply_text(
            "You already have an active research task. Please use /cancel to stop it first, or /status to check its progress."
        )
        return

    user = telegram_service.user_service.get_user(user_id)
    if user and user.successful_reports >= telegram_service.MAX_SUCCESSFUL_REPORTS:
        await update.message.reply_text(
            """We're sorry, but you've reached the maximum number of research reports!
            We're thrilled you've found this tool useful, feel free to let either Cam or Ewan know what you think of the tool.
            If you want more AI assisted research, check out http://perplexity.ai"""
        )
        return

    try:
        await update.message.reply_text(f"Starting research on: {research_question}")
        # Ensure research_question is stored as a string in context
        context.user_data["research_question"] = research_question
        await run_research_with_updates(telegram_service, update, context)
    except Exception as e:
        logging.error(f"Error in handle_start_research: {str(e)}")
        await update.message.reply_text(
            "There was an error with this research. Please try again."
        )


async def handle_workflow_event(
    telegram_service: TelegramService,
    event: Dict[str, Any],
    chat_id: int,
    agent_id: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    event_node: str = list(event.keys())[0]
    logging.info(f"Event node: {event_node}")
    telegram_service.agent_service.update_field(agent_id, "current_node", event_node)
    state: Any = event[event_node]

    # Check if the agent has been stopped
    if telegram_service.agent_service.get(agent_id).status == AgentStatus.CANCELLED:
        await telegram_service.send_message(chat_id=chat_id, text="Research stopped.")
        return

    if event_node == "type":
        error_message: Optional[str] = state
        if error_message:
            logging.error(f"Error in research process: {error_message}")
            await telegram_service.send_message(
                chat_id=chat_id,
                text=f"An error occurred during the research: {error_message}",
            )
            return

    if event_node == "final_report":
        await handle_final_report(
            telegram_service, state, chat_id, agent_id, update, context
        )
    else:
        # Get the summary from the state if available
        response_name = f"{event_node}_response"
        response = state.get(response_name)[-1]
        content = get_content(response)
        if content["summary"]:
            await telegram_service.send_message(
                chat_id=chat_id, text=content["summary"]
            )
        else:
            response = f"Processing {event_node}..."
            await telegram_service.send_message(chat_id=chat_id, text=response)


async def handle_final_report(
    telegram_service: TelegramService,
    state: Dict[str, Any],
    chat_id: int,
    agent_id: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    report: str = get_content(state.get("final_report_response"))
    await telegram_service.send_message(chat_id=chat_id, text="Beep boop, I'm done!")
    await telegram_service.send_message(chat_id=chat_id, text=report["content"])
    context.user_data.pop("research_state", None)
    user_id: str = str(update.effective_user.id)

    telegram_service.chat_history_service.clear_all_chat_history(user_id)
    telegram_service.agent_service.update_field(
        agent_id, "status", AgentStatus.COMPLETED
    )

    user = telegram_service.user_service.get_user(user_id)
    telegram_service.user_service.update_user(
        user_id, {"successful_reports": user.successful_reports + 1}
    )


async def run_research_with_updates(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    agent_id: Optional[str] = None
    try:
        chat_id: int = update.effective_chat.id
        user_id: str = str(update.effective_user.id)
        agent_id = telegram_service.user_service.get_user(user_id).agent_id

        research_question: str = context.user_data.get("research_question")
        telegram_service.agent_service.update_field(
            agent_id, "description", research_question
        )
        telegram_service.agent_service.update_field(
            agent_id, "status", AgentStatus.RUNNING
        )

        research_agent = ResearchAgent(send_message=telegram_service.send_message)
        initial_state: Dict[str, Any] = get_default_research_state(research_question)

        async for event in research_agent.async_stream(initial_state=initial_state):
            await handle_workflow_event(
                telegram_service, event, chat_id, agent_id, update, context
            )

    except Exception as e:
        if agent_id:
            telegram_service.agent_service.update_field(
                agent_id, "status", AgentStatus.ERROR
            )
            telegram_service.agent_service.update_field(agent_id, "error", str(e))

        context.user_data.pop("current_agent_id", None)
        context.user_data.pop("research_state", None)

        logging.error(f"Error in run_research_with_updates: {str(e)}")
        await telegram_service.send_message(
            chat_id=chat_id,
            text=f"There was an error with this research. Please try again.",
        )
