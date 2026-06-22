"""List command implementation."""

from timeline_cli.output_formatter import format_dates_list_markdown
from timeline_cli.storage import DEFAULT_STORAGE_FILE, read_timeline


def handle_list(args) -> None:
    """Handle list command - list all dates with counts."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Get sorted dates
    dates = sorted(timeline.records.keys())

    if not dates:
        print("No dates found")
        return

    # Build date counts data
    dates_data = {}
    for date in dates:
        record = timeline.records[date]
        dates_data[date] = {
            "events": len(record.events),
            "todos": len(record.todos),
            "notes": 1 if record.notes else 0,
        }

    print(format_dates_list_markdown(dates_data))
