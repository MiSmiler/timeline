"""Event command implementations."""

import sys

from timeline_cli.models import Event
from timeline_cli.output_formatter import OutputFormat, filter_by_contains, format_events
from timeline_cli.range_parser import filter_events_by_range, parse_range
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    collect_existing_ids,
    ensure_unique_id,
    find_event_by_prefix,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)


def handle_event_add(args) -> None:
    """Handle event add command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    record = get_or_create_daily_record(timeline, args.date)

    # Generate unique ID
    existing_ids = collect_existing_ids(timeline)
    event_id = ensure_unique_id(existing_ids, "e")

    # Create new event
    event = Event(
        time=args.time,
        text=args.text,
        details=args.detail or [],
        id=event_id,
    )

    # Add to record and sort by time
    record.events.append(event)
    record.events.sort(key=lambda e: e.time)

    # Write back
    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Added event [{event_id}]: {args.text} at {args.time}")


def handle_event_list(args) -> None:
    """Handle event list command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Use --range if provided
    if hasattr(args, "range") and args.range:
        date_range = parse_range(args.range)
        events_with_dates = filter_events_by_range(timeline.records, date_range)
        # Use --contains if provided
        if hasattr(args, "contains") and args.contains:
            events_with_dates = filter_by_contains(events_with_dates, args.contains)
    else:
        # Legacy: use positional date argument
        if not args.date or args.date not in timeline.records:
            print("No events found")
            return
        record = timeline.records[args.date]
        events_with_dates = [(args.date, e) for e in record.events]

        # Apply --contains filter if provided
        if hasattr(args, "contains") and args.contains:
            events_with_dates = filter_by_contains(events_with_dates, args.contains)

    # Determine output format
    # Legacy: --json or --simple override --output
    if hasattr(args, "json") and args.json:
        output_format = OutputFormat.JSON
    elif hasattr(args, "simple") and args.simple:
        output_format = OutputFormat.SIMPLE
    elif hasattr(args, "output"):
        output_format = OutputFormat(args.output)
    else:
        output_format = OutputFormat.TABLE

    # Output
    print(format_events(events_with_dates, output_format))


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
