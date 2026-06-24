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


def to_json_line(obj) -> str:
    """Convert object to JSON line with ensure_ascii=False.

    Args:
        obj: Any JSON-serializable object

    Returns:
        Single-line JSON string without indentation
    """
    return json.dumps(obj, ensure_ascii=False)


def _format_event_item(event: "Event", show_id: bool = False) -> str:
    """Format a single event item as markdown.

    Args:
        event: Event object
        show_id: Whether to show event ID

    Returns:
        Markdown formatted string for the event item
    """
    id_str = f"({event.id}) " if show_id and event.id else ""
    lines = [f"- {event.time} {id_str}{event.text}"]

    # Add details with 2-space indentation
    for detail in event.details:
        lines.append(f"  - {detail}")

    return "\n".join(lines)


def _format_todo_item(todo: "Todo", show_id: bool = False) -> str:
    """Format a single todo item as markdown.

    Args:
        todo: Todo object
        show_id: Whether to show todo ID

    Returns:
        Markdown formatted string for the todo item
    """
    # Status marker: checkbox format
    if todo.status == "completed":
        status_marker = "[x]"
    elif todo.status == "abandoned":
        status_marker = "[ ]"
    else:  # pending
        status_marker = "[ ]"

    # ID string
    id_str = f"({todo.id}) " if show_id and todo.id else ""

    # Time string (no placeholder for untimed)
    time_str = f"{todo.time} " if todo.time else ""

    # Text (with strikethrough for abandoned)
    text = f"~~{todo.text}~~" if todo.status == "abandoned" else todo.text

    lines = [f"- {status_marker} {time_str}{id_str}{text}"]

    # Add details with 2-space indentation
    for detail in todo.details:
        lines.append(f"  - {detail}")

    return "\n".join(lines)


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
    for date in sorted(groups.keys(), key=lambda d: (d is None, d or "")):
        # Use "Undated" for null date
        header = "# Undated" if date is None else f"# {date}"
        lines.append(header)

        for todo in groups[date]:
            # Format using component
            lines.append(_format_todo_item(todo, show_id))

        lines.append("")  # Blank line after each date group

    return "\n".join(lines).rstrip()


def format_todos_json(todos: list[tuple[str, "Todo"]]) -> str:
    """Format todos as JSONlines.

    Args:
        todos: List of (date, todo) tuples

    Returns:
        JSONlines string (one JSON object per line)
    """
    lines = []
    for date, todo in todos:
        data = {
            "id": todo.id,
            "date": date,
            "time": todo.time,
            "text": todo.text,
            "status": todo.status,
            "details": todo.details,
        }
        lines.append(to_json_line(data))
    return "\n".join(lines)


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
            # Format using component
            lines.append(_format_event_item(event, show_id))

        lines.append("")  # Blank line after each date group

    return "\n".join(lines).rstrip()


def format_events_json(events: list[tuple[str, "Event"]]) -> str:
    """Format events as JSONlines.

    Args:
        events: List of (date, event) tuples

    Returns:
        JSONlines string (one JSON object per line)
    """
    lines = []
    for date, event in events:
        data = {
            "id": event.id,
            "date": date,
            "time": event.time,
            "text": event.text,
            "details": event.details,
        }
        lines.append(to_json_line(data))
    return "\n".join(lines)


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


def format_dates_list_markdown(dates_data: dict[str, dict]) -> str:
    """Format dates list as markdown with counts.

    Args:
        dates_data: Dictionary mapping date to {"events": count, "todos": count, "notes": count}

    Returns:
        Markdown formatted string like:
        - 2026-06-17 (3 events, 5 todos, 1 note)
        - 2026-06-18 (2 events, 3 todos, 1 note)
    """
    if not dates_data:
        return "No dates found"

    lines = []
    for date in sorted(dates_data.keys()):
        counts = dates_data[date]
        event_count = counts.get("events", 0)
        todo_count = counts.get("todos", 0)
        note_count = counts.get("notes", 0)

        # Format: - YYYY-MM-DD (X event(s), Y todo(s), Z note(s))
        event_str = f"{event_count} event{'s' if event_count != 1 else ''}"
        todo_str = f"{todo_count} todo{'s' if todo_count != 1 else ''}"
        note_str = f"{note_count} note{'s' if note_count != 1 else ''}"

        lines.append(f"- {date} ({event_str}, {todo_str}, {note_str})")

    return "\n".join(lines)
