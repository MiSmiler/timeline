"""Diary command implementation - complete daily view."""

from timeline_cli.range_parser import normalize_date_string
from timeline_cli.storage import DEFAULT_STORAGE_FILE, read_timeline


def handle_diary(args) -> None:
    """Handle diary command - show complete daily view."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Normalize date argument
    date_str = normalize_date_string(args.date)

    # Get or create daily record
    record = timeline.records.get(date_str)

    # Output markdown
    print(format_diary_markdown(date_str, record, args.show_id))


def format_diary_markdown(date_str: str, record, show_id: bool = False) -> str:
    """Format a daily record as markdown.

    Args:
        date_str: Date string (YYYY-MM-DD)
        record: DailyRecord object or None
        show_id: Whether to show item IDs

    Returns:
        Markdown formatted string
    """
    lines = [f"# {date_str}", ""]

    # Event section
    lines.append("## Event")
    if record and record.events:
        for event in record.events:
            id_str = f"({event.id}) " if show_id and event.id else ""
            lines.append(f"- {event.time} {id_str}{event.text}")
            for detail in event.details:
                lines.append(f"    - {detail}")
    lines.append("")

    # TODO section
    lines.append("## TODO")
    if record and record.todos:
        for todo in record.todos:
            # Status marker
            if todo.status == "completed":
                status_marker = "[x]"
            elif todo.status == "abandoned":
                status_marker = "[ ]"
            else:  # pending
                status_marker = "[ ]"

            # ID string
            id_str = f"({todo.id}) " if show_id and todo.id else ""

            # Time string
            time_str = f"{todo.time} " if todo.time else ""

            # Text (with strikethrough for abandoned)
            text = f"~~{todo.text}~~" if todo.status == "abandoned" else todo.text

            lines.append(f"- {status_marker} {time_str}{id_str}{text}")
            for detail in todo.details:
                lines.append(f"    - {detail}")
    lines.append("")

    # Note section
    lines.append("## Note")
    if record and record.notes:
        lines.append(record.notes)
    lines.append("")

    return "\n".join(lines).rstrip()
