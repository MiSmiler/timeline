"""Note command implementations."""

from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)


def handle_note_add(args) -> None:
    """Handle note add command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    record = get_or_create_daily_record(timeline, args.date)

    # Set note (one note per date)
    record.notes = args.text

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Added note for {args.date}")


def handle_note_show(args) -> None:
    """Handle note show command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print("No note found")
        return

    record = timeline.records[args.date]
    if record.notes:
        print(record.notes)
    else:
        print("No note found")


def handle_note_edit(args) -> None:
    """Handle note edit command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    record = get_or_create_daily_record(timeline, args.date)

    # Update note
    record.notes = args.text

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Updated note for {args.date}")
