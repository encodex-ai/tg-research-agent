import json
from typing import List
from datetime import datetime, timezone
from textwrap import wrap
from langchain_core.messages import ChatMessage


# for getting the current date and time in UTC
def get_current_utc_datetime():
    now_utc = datetime.now(timezone.utc)
    current_time_utc = now_utc.strftime("%Y-%m-%d %H:%M:%S %Z")
    return current_time_utc


def custom_print(message, stdscr=None, scroll_pos=0):
    if stdscr:
        max_y, max_x = stdscr.getmaxyx()
        max_y -= 2  # Leave room for a status line at the bottom

        wrapped_lines = []
        for line in message.split("\n"):
            wrapped_lines.extend(wrap(line, max_x))

        num_lines = len(wrapped_lines)
        visible_lines = wrapped_lines[scroll_pos : scroll_pos + max_y]

        stdscr.clear()
        for i, line in enumerate(visible_lines):
            stdscr.addstr(i, 0, line[:max_x])

        stdscr.addstr(
            max_y,
            0,
            f"Lines {scroll_pos + 1} - {scroll_pos + len(visible_lines)} of {num_lines}",
        )
        stdscr.refresh()

        return num_lines
    else:
        print(message)


def format_chat_history(chat_history: List[ChatMessage]):
    formatted_history = []
    for message in chat_history:
        timestamp = message.additional_kwargs.get("timestamp")
        date_str = (
            timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "No timestamp"
        )
        # Use type(message).__name__ to get the role
        role = type(message).__name__.replace("Message", "").lower()
        if hasattr(message, "content") and message.content:
            formatted_history.append(f"{date_str} - {role}: {message.content}")
        else:
            formatted_history.append(f"{date_str} - {role}: {message}")
    return "\n".join(formatted_history)


def trim_state(state: dict, trim_count: int = 2):
    for key, value in state.items():
        # trim the values array if an array to the last 2.
        if isinstance(value, list):
            state[key] = value[-trim_count:]
    return state


def get_content(callable_or_value):
    # If it's callable, execute it
    if callable(callable_or_value):
        value = callable_or_value()
    else:
        value = callable_or_value

    # Check if the value is None or empty
    if not value:
        return None

    # Use check_for_content
    result = check_for_content(value)

    # Try to parse as JSON
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            # If it's not valid JSON, return the string as is
            return result
    else:
        return result


# for checking if an attribute of the state dict has "content".
def check_for_content(var):
    if var:
        try:
            var = var.content
            return var.content
        except:
            return var
    else:
        var
