"""Export command implementations."""

from pathlib import Path

from timeline_cli.storage import DEFAULT_STORAGE_FILE, read_timeline


def handle_export(args) -> None:
    """Handle export command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print(f"No record found for {args.date}")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    record = timeline.records[args.date]
    md_content = _format_as_markdown(record)

    output_file = output_dir / f"{args.date}.md"
    output_file.write_text(md_content)
    print(f"Exported: {output_file}")


def handle_export_all(args) -> None:
    """Handle export-all command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for date, record in timeline.records.items():
        md_content = _format_as_markdown(record)
        output_file = output_dir / f"{date}.md"
        output_file.write_text(md_content)
        print(f"Exported: {output_file}")


def _format_as_markdown(record) -> str:
    """Format a daily record as markdown."""
    lines = [f"# {record.date}", ""]

    # Events section
    if record.events:
        lines.append("## Events")
        for event in record.events:
            event_line = f"- {event.time} {event.text}"
            if event.details:
                event_line += "."
            lines.append(event_line)
            for detail in event.details:
                lines.append(f"    {detail}")
        lines.append("")

    # Todos section
    if record.todos:
        lines.append("## Todos")
        for todo in record.todos:
            if todo.status == "completed":
                checkbox = "[x]"
                text = todo.text
            elif todo.status == "abandoned":
                checkbox = "[ ]"
                text = f"~~{todo.text}~~"
            else:
                checkbox = "[ ]"
                text = todo.text

            time_str = f"{todo.time} " if todo.time else ""
            lines.append(f"- {checkbox} {time_str}{text}")
        lines.append("")

    # Notes section
    if record.notes:
        lines.append("## Notes")
        lines.append(record.notes)
        lines.append("")

    return "\n".join(lines).strip() + "\n"
