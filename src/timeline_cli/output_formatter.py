"""Output formatter for timeline-cli."""

import json
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from timeline_cli.models import Event, Todo


class OutputFormat(Enum):
    """Output format options."""

    MARKDOWN = "markdown"
    JSON = "json"


def format_todos_markdown(todos: list[tuple[str, "Todo"]], show_id: bool = False) -> str:
    """Format todos as markdown.

    Args:
        todos: List of (date, todo) tuples
        show_id: Whether to show todo ID

    Returns:
        Markdown formatted string
    """
    if not todos:
        return "No todos found"

    # Group by date
    groups: dict[str, list[Todo]] = {}
    for date, todo in todos:
        if date not in groups:
            groups[date] = []
        groups[date].append(todo)

    lines = []
    for date in sorted(groups.keys()):
        # Use "Undated" for null date
        header = "# Undated" if date == "0000-00-00" else f"# {date}"
        lines.append(header)

        for todo in groups[date]:
            # Format: [time] text or just text
            time_str = f"{todo.time} " if todo.time else "- "
            id_str = f"({todo.id}) " if show_id and todo.id else ""
            status_str = f"[{todo.status}]"
            lines.append(f"- {time_str}{id_str}{status_str} {todo.text}")

            # Add details indented
            for detail in todo.details:
                lines.append(f"  - {detail}")

        lines.append("")  # Blank line after each date group

    return "\n".join(lines).rstrip()


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


def format_todos(todos: list[tuple[str, "Todo"]], format: OutputFormat, show_id: bool = False) -> str:
    """Format todos according to output format.

    Args:
        todos: List of (date, todo) tuples
        format: Output format
        show_id: Whether to show todo ID (only for markdown)

    Returns:
        Formatted string
    """
    if format == OutputFormat.JSON:
        return format_todos_json(todos)
    else:
        return format_todos_markdown(todos, show_id)


def format_events_markdown(events: list[tuple[str, "Event"]], show_id: bool = False) -> str:
    """Format events as markdown.

    Args:
        events: List of (date, event) tuples
        show_id: Whether to show event ID

    Returns:
        Markdown formatted string
    """
    if not events:
        return "No events found"

    # Group by date
    groups: dict[str, list[Event]] = {}
    for date, event in events:
        if date not in groups:
            groups[date] = []
        groups[date].append(event)

    lines = []
    for date in sorted(groups.keys()):
        header = f"# {date}"
        lines.append(header)

        for event in groups[date]:
            # Format: time text
            id_str = f"({event.id}) " if show_id and event.id else ""
            lines.append(f"- {event.time} {id_str}{event.text}")

            # Add details indented
            for detail in event.details:
                lines.append(f"  - {detail}")

        lines.append("")  # Blank line after each date group

    return "\n".join(lines).rstrip()


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


def format_events(events: list[tuple[str, "Event"]], format: OutputFormat, show_id: bool = False) -> str:
    """Format events according to output format.

    Args:
        events: List of (date, event) tuples
        format: Output format
        show_id: Whether to show event ID (only for markdown)

    Returns:
        Formatted string
    """
    if format == OutputFormat.JSON:
        return format_events_json(events)
    else:
        return format_events_markdown(events, show_id)


def filter_by_contains(items: list[tuple[str, "Todo"] | tuple[str, "Event"]], text: str):
    """Filter items by substring match.

    Args:
        items: List of (date, todo/event) tuples
        text: Substring to search for

    Returns:
        Filtered list
    """
    return [(d, item) for d, item in items if text in item.text]
