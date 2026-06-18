"""Event command implementations."""

import sys

from timeline_cli.models import Event
from timeline_cli.output_formatter import OutputFormat, filter_by_contains, format_events
from timeline_cli.range_parser import filter_events_by_range, parse_range
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    collect_existing_ids,
    ensure_unique_id,
    find_event_by_id_in_timeline,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)


def handle_event_add(args) -> None:
    """Handle event add command (Issue #46: TEXT --date DATE --time TIME)."""
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
    print(f"[{event_id}] Added: {args.text} at {args.time}")


def handle_event_list(args) -> None:
    """Handle event list command (Issue #46: --range required)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Use --range (now required)
    date_range = parse_range(args.range)
    events_with_dates = filter_events_by_range(timeline.records, date_range)

    # Apply additional filters
    if hasattr(args, "contains") and args.contains:
        events_with_dates = filter_by_contains(events_with_dates, args.contains)

    # Determine output format
    output_format = OutputFormat(args.output)

    # Output
    print(format_events(events_with_dates, output_format))


def handle_event_edit(args) -> None:
    """Handle event edit command (Issue #46: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_event_by_id_in_timeline(timeline, args.id)

    if result is None:
        print(f"Error: Event not found with ID '{args.id}'", file=sys.stderr)
        sys.exit(1)

    date, record, idx, event = result

    # Track changes for diff-style output
    changes = []

    # Apply edits and track changes
    if args.new_text:
        old_text = event.text
        event.text = args.new_text
        changes.append(("text", old_text, args.new_text))

    if args.new_time:
        old_time = event.time
        event.time = args.new_time
        changes.append(("time", old_time, args.new_time))

    if args.append_detail:
        event.details.append(args.append_detail)
        changes.append(("detail", None, args.append_detail, "append"))

    if args.set_detail:
        old_details = ", ".join(event.details) if event.details else "(no details)"
        new_details = ", ".join(args.set_detail)
        event.details = args.set_detail
        changes.append(("details", old_details, new_details))

    # Re-sort if time changed
    if args.new_time:
        record.events.sort(key=lambda e: e.time)

    write_timeline(timeline, DEFAULT_STORAGE_FILE)

    # Git-style output
    if len(changes) == 1:
        # Single change: concise format
        change_type, old, new = changes[0][0], changes[0][1], changes[0][2]
        if change_type == "text":
            print(f"[{args.id}] Edited: {old} → {new}")
        elif change_type == "time":
            print(f"[{args.id}] Edited: time: {old} → {new}")
        elif change_type == "details":
            print(f"[{args.id}] Edited: details: {old} → {new}")
        elif change_type == "detail" and changes[0][3] == "append":
            print(f"[{args.id}] Edited: + detail: {new}")
    elif len(changes) > 1:
        # Multiple changes: multi-line diff
        print(f"[{args.id}] Edited:")
        for change in changes:
            change_type = change[0]
            if change_type == "text":
                print(f"  text: {change[1]} → {change[2]}")
            elif change_type == "time":
                print(f"  time: {change[1]} → {change[2]}")
            elif change_type == "details":
                print(f"  details: {change[1]} → {change[2]}")
            elif change_type == "detail" and change[3] == "append":
                print(f"  + detail: {change[2]}")


def handle_event_delete(args) -> None:
    """Handle event delete command (Issue #46: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_event_by_id_in_timeline(timeline, args.id)

    if result is None:
        print(f"Error: Event not found with ID '{args.id}'", file=sys.stderr)
        sys.exit(1)

    date, record, idx, event = result

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
    print(f"[{args.id}] Deleted: {event.text}")
