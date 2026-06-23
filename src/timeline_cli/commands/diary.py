"""Diary command implementation - complete daily view."""

from timeline_cli.output_formatter import _format_event_item, _format_todo_item
from timeline_cli.storage import DEFAULT_STORAGE_FILE, read_timeline
from timeline_cli.time_expr import normalize_date_string


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
            # Use shared formatting component
            lines.append(_format_event_item(event, show_id))
    lines.append("")

    # TODO section
    lines.append("## TODO")
    if record and record.todos:
        for todo in record.todos:
            # Use shared formatting component
            lines.append(_format_todo_item(todo, show_id))
    lines.append("")

    # Note section
    lines.append("## Note")
    if record and record.notes:
        lines.append(record.notes)
    lines.append("")

    return "\n".join(lines).rstrip()
