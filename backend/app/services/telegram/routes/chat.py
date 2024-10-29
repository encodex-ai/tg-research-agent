import logging
from typing import Dict, Any
from app.agents.chat_agent.state import get_default_chat_state
from app.agents.chat_agent.chat_agent import ChatAgent
from telegram import Update
from telegram.ext import ContextTypes
from app.utils.helper_functions import get_content
from app.services.telegram.service import TelegramService
from app.models.agent import AgentStatus
from langchain_community.chat_message_histories import (
    ChatMessageHistory,
)  # Updated import


async def process_message_with_chat_agent(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Process user messages using the chat agent.
    """
    try:
        user_id: str = str(update.effective_user.id)
        message: str = update.message.text
        chat_id: int = update.effective_chat.id

        # Check if the user has passed the limit for reports
        user = telegram_service.user_service.get_user(user_id)
        if user and user.successful_reports >= telegram_service.MAX_SUCCESSFUL_REPORTS:
            await update.message.reply_text(
                """We're sorry, but you've reached the maximum number of research reports!
                We're thrilled you've found this tool useful, feel free to let either Cam or Ewan know what you think of the tool.
                If you want more AI assisted research, check out http://perplexity.ai"""
            )
            return

        # Save the user's message to chat history
        telegram_service.chat_history_service.add_message(user_id, "user", message)
        chat_history: ChatMessageHistory = (
            telegram_service.chat_history_service.get_langchain_chat_history(user_id)
        )

        initial_state: Dict[str, Any] = get_default_chat_state(
            chat_id=chat_id,
            current_message=message,
            chat_history=chat_history,
            agent_id=user.agent_id,
        )
        chat_agent = ChatAgent(send_message=telegram_service.send_message)

        async for event in chat_agent.async_stream(initial_state=initial_state):
            await handle_workflow_event(
                telegram_service,
                update,
                context,
                event,
                chat_id,
                user_id,
            )

    except Exception as e:
        logging.error(f"Error in process_message_with_chat_agent: {str(e)}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your message."
        )


async def handle_workflow_event(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    event: Dict[str, Any],
    chat_id: str,
    user_id: str,
):
    event_node = list(event.keys())[0]
    logging.info(f"Event node: {event_node}")
    state = event[event_node]

    if event_node == "finalizer":
        await handle_finalizer_output(telegram_service, update, context, state)
    else:
        # Get the summary from the state if available
        response_name = f"{event_node}_response"
        response = state.get(response_name)
        if response:
            content = get_content(response[-1])
            if content and "summary" in content:
                await telegram_service.send_message(
                    chat_id=chat_id, text=content["summary"]
                )
            else:
                await telegram_service.send_message(
                    chat_id=chat_id, text=f"Processing {event_node}..."
                )


async def handle_finalizer_output(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    state: Dict[str, Any],
):
    finalized_response = get_content(state.get("finalizer_response"))
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)

    if not finalized_response:
        await telegram_service.send_message(
            chat_id=chat_id,
            text="I'm sorry, I don't understand. Please try again.",
        )
        telegram_service.chat_history_service.add_message(
            str(update.effective_user.id),
            "assistant",
            "I'm sorry, I don't understand. Please try again.",
        )
        return

    if (
        "clarifying_question" in finalized_response
        and finalized_response["clarifying_question"]
    ):
        await telegram_service.send_message(
            chat_id=chat_id, text=finalized_response["clarifying_question"]
        )
        telegram_service.chat_history_service.add_message(
            user_id,
            "assistant",
            f"Clarifying question: {finalized_response['clarifying_question']}",
            is_clarification=True,
        )
    elif "final_report" in finalized_response and finalized_response["final_report"]:
        await telegram_service.send_message(
            chat_id=chat_id, text=finalized_response["final_report"]
        )
        telegram_service.user_service.update_user(user_id, {"successful_reports": 1})

        await telegram_service.send_message(
            chat_id=chat_id, text="Clearing internal message history..."
        )
        telegram_service.chat_history_service.clear_all_chat_history(user_id)
    elif "function_name" in finalized_response and finalized_response["function_name"]:
        await handle_function_call(
            telegram_service, update, context, finalized_response["function_name"]
        )
        telegram_service.chat_history_service.add_message(
            user_id,
            "assistant",
            f"Function call: /{finalized_response['function_name']}",
        )


async def handle_function_call(
    telegram_service: TelegramService,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    function_name: str,
) -> None:
    """
    Handle function calls from the chat agent.
    """
    logging.info(f"Function call: {function_name}")

    if function_name == "help":
        from .help import help_command

        await help_command(telegram_service, update, context)
    elif function_name == "status":
        from .status import status_command

        await status_command(telegram_service, update, context)
    elif function_name == "cancel":
        from .cancel import cancel_command

        await cancel_command(telegram_service, update, context)
    elif function_name == "start":
        from .start import start_command

        await start_command(telegram_service, update, context)
    else:
        await update.message.reply_text(f"Unknown function: {function_name}")
