"""Event command implementations."""

import sys
from datetime import date, datetime

from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Event
from timeline_cli.output_formatter import OutputFormat, filter_by_contains, format_events
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    collect_existing_ids,
    ensure_unique_id,
    find_event_by_id_in_timeline,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)
from timeline_cli.time_expr import DateRange, TimeExpr, filter_events_by_range


def handle_event_add(args) -> None:
    """Handle event add command (Issue #83: TimeExpr for --at)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Parse --at parameter using TimeExpr
    time_expr = TimeExpr.parse(args.at)

    # Reject timerange for add (only timepoint allowed)
    if time_expr.kind == "timerange":
        raise TimelineValidationError(
            "Cannot use timerange for --at in add command. "
            "Use a timepoint like 'todayT09:00', 'now', or 'YYYY-MM-DDT10:00'."
        )

    tp = time_expr.timepoint

    # Event must have time component
    if tp.is_undated:
        raise TimelineValidationError(
            "Event cannot be undated. Use '--at YYYY-MM-DDTHH:MM' or '--at HH:MM' (defaults to today)."
        )

    if not tp.has_time_component():
        raise TimelineValidationError(
            "Event must have a time component.\n"
            "Use '--at YYYY-MM-DDTHH:MM' or '--at HH:MM' (defaults to today).\n"
            f'Received: --at "{args.at}" (parsed as date-only).'
        )

    # Get concrete date/time
    dt = tp.to_datetime()
    if dt is None:
        raise TimelineValidationError("Event must have a valid datetime.")

    # Validate: Event cannot be in future (check using current time)
    now = datetime.now()
    if dt > now:
        raise TimelineValidationError(
            f"Event time cannot be later than now.\n"
            f"Specified: {dt.strftime('%Y-%m-%d %H:%M')}, Current: {now.strftime('%Y-%m-%d %H:%M')}"
        )

    normalized_date = dt.date().isoformat()
    normalized_time = dt.strftime("%H:%M")

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

    # Git-style output
    print(f"[{event_id}] Added: {args.text} ({normalized_date} {normalized_time})")


def handle_event_list(args) -> None:
    """Handle event list command (Issue #81: --at parameter, parameter requirement)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Parameter requirement: at least one of --at, --contains
    has_params = args.at is not None or (hasattr(args, "contains") and args.contains is not None)

    if not has_params:
        raise TimelineValidationError(
            "At least one parameter required: --at or --contains.\n"
            "This prevents accidental output of all events.\n"
            "Use '--at ..' to list all events explicitly."
        )

    # Determine date range from --at parameter
    if args.at:
        time_expr = TimeExpr.parse(args.at)

        # Reject undated for events
        if time_expr.kind == "timepoint" and time_expr.timepoint.is_undated:
            raise TimelineValidationError(
                "Events cannot be undated. Use '--at ..' to list all events, or specify a date/time range."
            )

        if time_expr.kind == "timerange":
            date_range = time_expr.timerange.expand_for_query()
        else:
            # Timepoint: expand to full day range for list commands
            tp = time_expr.timepoint
            from datetime import time

            if tp.time is None:
                # Date-only: expand to full day
                date_obj = tp.to_datetime()
                if date_obj:
                    date_range = DateRange(
                        start=datetime.combine(date_obj, time.min),
                        end=datetime.combine(date_obj, time.max.replace(microsecond=0)),
                    )
                else:
                    date_range = DateRange()
            else:
                # Has time: exact match
                dt = tp.to_datetime()
                date_range = DateRange(start=dt, end=dt)
    else:
        # No --at: default to all dates (..)
        date_range = DateRange()

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
    """Handle event edit command (Issue #83: TimeExpr for --new-at)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_event_by_id_in_timeline(timeline, args.id)

    if result is None:
        raise TimelineValidationError(f"Event not found: {args.id}")

    old_date, record, idx, event = result

    # Track changes for diff-style output
    changes = []

    # Handle --new-at parameter (Issue #83)
    if args.new_at is not None:
        time_expr = TimeExpr.parse(args.new_at)

        # Reject timerange for edit (only timepoint allowed)
        if time_expr.kind == "timerange":
            raise TimelineValidationError(
                "Cannot use timerange for --new-at in edit command. "
                "Use a timepoint like 'todayT09:00', 'now', or 'YYYY-MM-DDT10:00'."
            )

        tp = time_expr.timepoint

        # Event must have time component
        if tp.is_undated:
            raise TimelineValidationError(
                "Event cannot be undated. Use '--new-at YYYY-MM-DDTHH:MM' or '--new-at HH:MM'."
            )

        if not tp.has_time_component():
            raise TimelineValidationError(
                "Event must have a time component.\n"
                "Use '--new-at YYYY-MM-DDTHH:MM' or '--new-at HH:MM'.\n"
                f'Received: --new-at "{args.new_at}" (parsed as date-only).'
            )

        # Get concrete date/time
        dt = tp.to_datetime()
        if dt is None or (type(dt) is date):
            raise TimelineValidationError("Event must have a valid datetime.")

        # Validate: Event cannot be in future
        now = datetime.now()
        if dt > now:
            raise TimelineValidationError(
                f"Event time cannot be later than now.\n"
                f"Specified: {dt.strftime('%Y-%m-%d %H:%M')}, Current: {now.strftime('%Y-%m-%d %H:%M')}"
            )

        new_date = dt.date().isoformat()
        new_time = dt.strftime("%H:%M")

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
