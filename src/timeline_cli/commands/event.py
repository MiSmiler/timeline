"""Event command implementations."""

import sys

from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Event
from timeline_cli.output_formatter import OutputFormat, filter_by_contains, format_events
from timeline_cli.range_parser import (
    filter_events_by_range,
    parse_at_parameter,
    parse_range,
    validate_event_time_not_future,
)
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
    """Handle event add command (Issue #70: TEXT --at AT)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Parse --at parameter
    at_param = parse_at_parameter(args.at)

    # Event model constraint: must have time
    if at_param.time is None:
        raise TimelineValidationError(
            "Event must have a time.\n"
            "Use '--at \"YYYY-MM-DD HH:MM\"' or '--at \"HH:MM\"' (defaults to today).\n"
            f'Received: --at "{args.at}" (parsed as date-only).'
        )

    # Validate Event time is not in the future (Issue #70)
    validate_event_time_not_future(at_param)

    # Determine normalized date and time
    normalized_date = at_param.date if at_param.date else "0000-00-00"
    normalized_time = at_param.time

    record = get_or_create_daily_record(timeline, normalized_date)

    # Generate unique ID
    existing_ids = collect_existing_ids(timeline)
    event_id = ensure_unique_id(existing_ids, "e")

    # Create new event
    event = Event(
        time=normalized_time,
        text=args.text,
        details=args.detail or [],
        id=event_id,
    )

    # Add to record and sort by time
    record.events.append(event)
    record.events.sort(key=lambda e: e.time)

    # Write back
    write_timeline(timeline, DEFAULT_STORAGE_FILE)

    # Git-style output with normalized date and time (Issue #68, #70)
    print(f"[{event_id}] Added: {args.text} ({normalized_date} {normalized_time})")


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
    output_format = OutputFormat.JSON if getattr(args, "json", False) else OutputFormat.MARKDOWN
    show_id = getattr(args, "show_id", False)

    # Handle empty results for JSON format
    if output_format == OutputFormat.JSON and not events_with_dates:
        print("No events found for the specified range", file=sys.stderr)
        return

    # Output
    print(format_events(events_with_dates, output_format, show_id))


def handle_event_edit(args) -> None:
    """Handle event edit command (Issue #70: use --id, --new-at)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_event_by_id_in_timeline(timeline, args.id)

    if result is None:
        raise TimelineValidationError(f"Event not found: {args.id}")

    old_date, record, idx, event = result

    # Track changes for diff-style output
    changes = []

    # Handle --new-at parameter (Issue #70)
    # Note: args.new_at can be "" (empty string) for time-only changes
    if args.new_at is not None:
        at_param = parse_at_parameter(args.new_at)

        # Event model constraint: must have time
        if at_param.time is None:
            raise TimelineValidationError(
                "Event must have a time.\n"
                "Use '--new-at \"YYYY-MM-DD HH:MM\"' or '--new-at \"HH:MM\"'.\n"
                f'Received: --new-at "{args.new_at}" (parsed as date-only).'
            )

        # Validate Event time is not in the future (Issue #70)
        validate_event_time_not_future(at_param)

        new_date = at_param.date if at_param.date else "0000-00-00"
        new_time = at_param.time

        # Track date/time changes
        old_time_str = event.time

        # If date changed, need to move event to different record
        if new_date != old_date:
            # Remove from old record
            record.events.pop(idx)

            # Get or create new record
            new_record = get_or_create_daily_record(timeline, new_date)

            # Update event's time
            event.time = new_time

            # Add to new record and sort
            new_record.events.append(event)
            new_record.events.sort(key=lambda e: e.time)

            # Track changes
            changes.append(("date", old_date, new_date))
            if old_time_str != new_time:
                changes.append(("time", old_time_str, new_time))
        else:
            # Same date, just update time
            if new_time != event.time:
                event.time = new_time
                changes.append(("time", old_time_str, new_time))
                record.events.sort(key=lambda e: e.time)

    # Apply other edits and track changes
    if args.new_text:
        old_text = event.text
        event.text = args.new_text
        changes.append(("text", old_text, args.new_text))

    if args.append_detail:
        # Issue #54: Support multiple --append-detail calls
        for detail in args.append_detail:
            event.details.append(detail)
            changes.append(("detail", None, detail, "append"))
    if args.set_detail:
        # Issue #54: Parse \n-separated details
        old_details = ", ".join(event.details) if event.details else "(no details)"
        new_details = ", ".join([line for line in args.set_detail.split("\n") if line.strip()])
        event.details = [line for line in args.set_detail.split("\n") if line.strip()]
        changes.append(("details", old_details, new_details))

    # Re-sort if time changed via --new-at (already handled above)
    # Note: sorting is done inline when time is updated

    write_timeline(timeline, DEFAULT_STORAGE_FILE)

    # Git-style output
    if len(changes) == 1:
        # Single change: concise format
        change_type, old, new = changes[0][0], changes[0][1], changes[0][2]
        if change_type == "text":
            print(f"[{args.id}] Edited: {old} → {new}")
        elif change_type == "time":
            print(f"[{args.id}] Edited: time: {old} → {new}")
        elif change_type == "date":
            print(f"[{args.id}] Edited: date: {old} → {new}")
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
            elif change_type == "date":
                print(f"  date: {change[1]} → {change[2]}")
            elif change_type == "details":
                print(f"  details: {change[1]} → {change[2]}")
            elif change_type == "detail" and change[3] == "append":
                print(f"  + detail: {change[2]}")


def handle_event_delete(args) -> None:
    """Handle event delete command (Issue #46: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_event_by_id_in_timeline(timeline, args.id)

    if result is None:
        raise TimelineValidationError(f"Event not found: {args.id}")

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
