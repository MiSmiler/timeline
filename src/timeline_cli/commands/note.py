"""Note command implementations."""

from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)
from timeline_cli.time_expr import normalize_date_string


def handle_note_add(args) -> None:
    """Handle note add command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    # Normalize relative date keywords to YYYY-MM-DD format
    normalized_date = normalize_date_string(args.date)
    record = get_or_create_daily_record(timeline, normalized_date)

    # Set note (one note per date)
    record.notes = args.text

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Added note for {normalized_date}")


def handle_note_show(args) -> None:
    """Handle note show command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    # Normalize relative date keywords to YYYY-MM-DD format
    normalized_date = normalize_date_string(args.date)

    if normalized_date not in timeline.records:
        print("No note found")
        return

    record = timeline.records[normalized_date]
    if record.notes:
        print(record.notes)
    else:
        print("No note found")


def handle_note_edit(args) -> None:
    """Handle note edit command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    # Normalize relative date keywords to YYYY-MM-DD format
    normalized_date = normalize_date_string(args.date)
    record = get_or_create_daily_record(timeline, normalized_date)

    # Update note
    record.notes = args.text

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Updated note for {normalized_date}")
