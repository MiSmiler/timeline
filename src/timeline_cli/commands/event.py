"""Event command implementations."""

import sys

from timeline_cli.models import Event
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    find_event_by_prefix,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)


def handle_event_add(args) -> None:
    """Handle event add command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    record = get_or_create_daily_record(timeline, args.date)

    # Create new event
    event = Event(
        time=args.time,
        text=args.text,
        details=args.detail or [],
    )

    # Add to record and sort by time
    record.events.append(event)
    record.events.sort(key=lambda e: e.time)

    # Write back
    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Added event: {args.text} at {args.time}")


def handle_event_list(args) -> None:
    """Handle event list command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print("No events found")
        return

    record = timeline.records[args.date]
    events = record.events

    if args.json:
        import json

        data = [
            {
                "time": e.time,
                "text": e.text,
                "details": e.details,
            }
            for e in events
        ]
        print(json.dumps(data, indent=2))
    elif args.simple:
        for event in events:
            print(f"{event.time} {event.text}")
    else:
        # Default table format
        if not events:
            print("No events found")
            return
        print(f"{'Time':<8} {'Text'}")
        print("-" * 40)
        for event in events:
            print(f"{event.time:<8} {event.text}")


def handle_event_edit(args) -> None:
    """Handle event edit command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print(f"Error: No record found for {args.date}", file=sys.stderr)
        sys.exit(1)

    record = timeline.records[args.date]
    result = find_event_by_prefix(record, args.time, args.text_prefix)

    if result is None:
        print("Error: Event not found or ambiguous", file=sys.stderr)
        sys.exit(1)

    idx, event = result

    # Apply edits
    if args.new_text:
        event.text = args.new_text
    if args.new_time:
        event.time = args.new_time
    if args.append_detail:
        event.details.append(args.append_detail)
    if args.set_detail:
        event.details = args.set_detail

    # Re-sort if time changed
    if args.new_time:
        record.events.sort(key=lambda e: e.time)

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Edited: {event.text}")


def handle_event_delete(args) -> None:
    """Handle event delete command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print(f"Error: No record found for {args.date}", file=sys.stderr)
        sys.exit(1)

    record = timeline.records[args.date]
    result = find_event_by_prefix(record, args.time, args.text_prefix)

    if result is None:
        print("Error: Event not found or ambiguous", file=sys.stderr)
        sys.exit(1)

    idx, event = result

    # Check confirmation (skip with --yes)
    if not args.yes:
        print(f"Delete '{event.text}'? [y/N]: ")
        response = input().strip().lower()
        if response != "y":
            print("Cancelled")
            return

    # Remove event
    record.events.pop(idx)

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Deleted: {event.text}")
