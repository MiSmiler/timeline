"""Output formatter for timeline-cli --output parameter."""

import json
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from timeline_cli.models import Event, Todo


class OutputFormat(Enum):
    """Output format options."""

    TABLE = "table"
    JSON = "json"
    SIMPLE = "simple"


def format_todos_table(todos: list[tuple[str, "Todo"]]) -> str:
    """Format todos as table.

    Args:
        todos: List of (date, todo) tuples

    Returns:
        Formatted table string
    """
    if not todos:
        return "No todos found"

    # Check if any todo has ID
    has_id = any(todo.id for _, todo in todos)

    if has_id:
        lines = [f"{'ID':<8} {'Date':<12} {'Time':<8} {'Status':<10} {'Text'}"]
        lines.append("-" * 60)
        for date, todo in todos:
            id_str = todo.id or "-"
            time_str = todo.time or "-"
            lines.append(f"{id_str:<8} {date:<12} {time_str:<8} {todo.status:<10} {todo.text}")
    else:
        lines = [f"{'Date':<12} {'Time':<8} {'Status':<10} {'Text'}"]
        lines.append("-" * 50)
        for date, todo in todos:
            time_str = todo.time or "-"
            lines.append(f"{date:<12} {time_str:<8} {todo.status:<10} {todo.text}")

    return "\n".join(lines)


def format_todos_json(todos: list[tuple[str, "Todo"]]) -> str:
    """Format todos as JSON.

    Args:
        todos: List of (date, todo) tuples

    Returns:
        JSON string
    """
    data = [
        {
            "id": todo.id,
            "date": date,
            "time": todo.time,
            "text": todo.text,
            "status": todo.status,
            "details": todo.details,
        }
        for date, todo in todos
    ]
    return json.dumps(data, indent=2)


def format_todos_simple(todos: list[tuple[str, "Todo"]]) -> str:
    """Format todos as simple text.

    Args:
        todos: List of (date, todo) tuples

    Returns:
        Simple text string
    """
    lines = []
    for date, todo in todos:
        id_str = f"[{todo.id}] " if todo.id else ""
        time_str = todo.time or "undated"
        status_str = f"[{todo.status}]"
        lines.append(f"{id_str}{date} {time_str} {status_str} {todo.text}")
    return "\n".join(lines)


def format_todos(todos: list[tuple[str, "Todo"]], format: OutputFormat) -> str:
    """Format todos according to output format.

    Args:
        todos: List of (date, todo) tuples
        format: Output format

    Returns:
        Formatted string
    """
    if format == OutputFormat.JSON:
        return format_todos_json(todos)
    elif format == OutputFormat.SIMPLE:
        return format_todos_simple(todos)
    else:
        return format_todos_table(todos)


def format_events_table(events: list[tuple[str, "Event"]]) -> str:
    """Format events as table.

    Args:
        events: List of (date, event) tuples

    Returns:
        Formatted table string
    """
    if not events:
        return "No events found"

    # Check if any event has ID
    has_id = any(event.id for _, event in events)

    if has_id:
        lines = [f"{'ID':<8} {'Date':<12} {'Time':<8} {'Text'}"]
        lines.append("-" * 50)
        for date, event in events:
            id_str = event.id or "-"
            lines.append(f"{id_str:<8} {date:<12} {event.time:<8} {event.text}")
    else:
        lines = [f"{'Date':<12} {'Time':<8} {'Text'}"]
        lines.append("-" * 40)
        for date, event in events:
            lines.append(f"{date:<12} {event.time:<8} {event.text}")

    return "\n".join(lines)


def format_events_json(events: list[tuple[str, "Event"]]) -> str:
    """Format events as JSON.

    Args:
        events: List of (date, event) tuples

    Returns:
        JSON string
    """
    data = [
        {
            "id": event.id,
            "date": date,
            "time": event.time,
            "text": event.text,
            "details": event.details,
        }
        for date, event in events
    ]
    return json.dumps(data, indent=2)


def format_events_simple(events: list[tuple[str, "Event"]]) -> str:
    """Format events as simple text.

    Args:
        events: List of (date, event) tuples

    Returns:
        Simple text string
    """
    lines = []
    for date, event in events:
        id_str = f"[{event.id}] " if event.id else ""
        lines.append(f"{id_str}{date} {event.time} {event.text}")
    return "\n".join(lines)


def format_events(events: list[tuple[str, "Event"]], format: OutputFormat) -> str:
    """Format events according to output format.

    Args:
        events: List of (date, event) tuples
        format: Output format

    Returns:
        Formatted string
    """
    if format == OutputFormat.JSON:
        return format_events_json(events)
    elif format == OutputFormat.SIMPLE:
        return format_events_simple(events)
    else:
        return format_events_table(events)


def filter_by_contains(items: list[tuple[str, "Todo"] | tuple[str, "Event"]], text: str):
    """Filter items by substring match.

    Args:
        items: List of (date, todo/event) tuples
        text: Substring to search for

    Returns:
        Filtered list
    """
    return [(d, item) for d, item in items if text in item.text]
