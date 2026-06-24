"""Todo command implementations."""

import sys
from datetime import datetime

from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Todo
from timeline_cli.output_formatter import OutputFormat, filter_by_contains, format_todos
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    collect_existing_ids,
    ensure_unique_id,
    find_todo_by_id_in_timeline,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)
from timeline_cli.time_expr import DateRange, TimeExpr, filter_todos_by_range


def handle_todo_add(args) -> None:
    """Handle todo add command (Issue #83: TimeExpr for --at)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Parse --at parameter using TimeExpr
    time_expr = TimeExpr.parse(args.at)

    # Determine normalized date and time
    if time_expr.kind == "timerange" and time_expr.timerange.is_undated:
        # Special case: undated (Timerange keyword)
        normalized_date = None
        normalized_time = None
    elif time_expr.kind == "timerange":
        # Regular timerange - reject for add
        raise TimelineValidationError(
            "Cannot use timerange for --at in add command. "
            "Use a timepoint like 'todayT09:00', 'today', 'undated', or 'now'."
        )
    else:
        # Timepoint
        tp = time_expr.timepoint
        if tp.is_undated:
            normalized_date = None
            normalized_time = None
        else:
            # Get concrete date/time from timepoint
            dt = tp.to_datetime()
            if dt is None:
                # Empty timepoint - treat as undated
                normalized_date = None
                normalized_time = None
            elif isinstance(dt, datetime):
                normalized_date = dt.date().isoformat()
                normalized_time = dt.strftime("%H:%M")
            else:
                # Date only
                normalized_date = dt.isoformat()
                normalized_time = None

    record = get_or_create_daily_record(timeline, normalized_date)

    # Generate unique ID
    existing_ids = collect_existing_ids(timeline)
    todo_id = ensure_unique_id(existing_ids, "t")

    # Create new todo
    todo = Todo(
        time=normalized_time,
        text=args.text,
        status="pending",
        details=args.detail or [],
        id=todo_id,
    )

    # Add to record and sort by time
    record.todos.append(todo)
    _sort_todos(record.todos)

    # Write back
    write_timeline(timeline, DEFAULT_STORAGE_FILE)

    # Git-style output with normalized date and time
    if normalized_date is None:
        print(f"[{todo_id}] Added: {args.text} (undated)")
    elif normalized_time:
        print(f"[{todo_id}] Added: {args.text} ({normalized_date} {normalized_time})")
    else:
        print(f"[{todo_id}] Added: {args.text} ({normalized_date} no-time)")


def handle_todo_list(args) -> None:
    """Handle todo list command (Issue #81, #82: --at, --no-time, parameter requirement)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Parameter requirement: at least one of --at, --no-time, --status, --contains
    has_params = (
        args.at is not None
        or getattr(args, "no_time", False)
        or args.status is not None
        or (hasattr(args, "contains") and args.contains is not None)
    )

    if not has_params:
        raise TimelineValidationError(
            "At least one parameter required: --at, --no-time, --status, or --contains.\n"
            "This prevents accidental output of all todos.\n"
            "Use '--at ..' to list all todos explicitly."
        )

    # Determine date range from --at parameter
    todos_with_dates = []

    if args.at:
        time_expr = TimeExpr.parse(args.at)

        # Handle undated as special Timerange keyword
        if time_expr.kind == "timerange" and time_expr.timerange.is_undated:
            # For undated: filter only items with date=None
            for date_str, record in timeline.records.items():
                if date_str is None:
                    for todo in record.todos:
                        todos_with_dates.append((date_str, todo))
        elif time_expr.kind == "timerange":
            date_range = time_expr.timerange.expand_for_query()
            todos_with_dates = filter_todos_by_range(timeline.records, date_range)
        else:
            # Timepoint: expand to full day range for list commands
            # (date-only -> dateT00:00..dateT23:59, time-only -> exact match today)
            tp = time_expr.timepoint
            if tp.time is None:
                # Date-only: expand to full day
                from datetime import time

                date_obj = tp.to_datetime()
                if date_obj:
                    date_range = DateRange(
                        start=datetime.combine(date_obj, time.min),
                        end=datetime.combine(date_obj, time.max.replace(microsecond=0)),
                        include_undated=False,
                    )
                else:
                    date_range = DateRange()  # Empty timepoint -> all (shouldn't happen)
                todos_with_dates = filter_todos_by_range(timeline.records, date_range)
            else:
                # Has time: exact match - filter todos with exact time on that date
                dt = tp.to_datetime()
                target_date = dt.date().isoformat() if isinstance(dt, datetime) else dt.isoformat()
                target_time = dt.strftime("%H:%M") if isinstance(dt, datetime) else None
                if target_date in timeline.records:
                    for todo in timeline.records[target_date].todos:
                        if todo.time == target_time:
                            todos_with_dates.append((target_date, todo))
    else:
        # No --at: default to all dates (..)
        date_range = DateRange()
        todos_with_dates = filter_todos_by_range(timeline.records, date_range)

    # Apply --no-time filter (Issue #82)
    if getattr(args, "no_time", False):
        # Validate: --no-time cannot be combined with timepoint (exact time match)
        if args.at:
            time_expr = TimeExpr.parse(args.at)
            if time_expr.kind == "timepoint" and time_expr.timepoint.time is not None:
                raise TimelineValidationError(
                    "--no-time cannot be used with exact time match (--at with time).\n"
                    "Use '--at today' (date-only) or '--at today..' (timerange) instead."
                )
        # Filter todos without time component
        todos_with_dates = [(d, t) for d, t in todos_with_dates if t.time is None]

    # Apply additional filters
    if args.status:
        todos_with_dates = [(d, t) for d, t in todos_with_dates if t.status == args.status]
    if hasattr(args, "contains") and args.contains:
        todos_with_dates = filter_by_contains(todos_with_dates, args.contains)

    # Determine output format
    output_format = OutputFormat.JSON if getattr(args, "json", False) else OutputFormat.MARKDOWN
    show_id = getattr(args, "show_id", False)

    # Handle empty results for JSON format
    if output_format == OutputFormat.JSON and not todos_with_dates:
        print("No todos found for the specified range", file=sys.stderr)
        return

    # Output
    print(format_todos(todos_with_dates, output_format, show_id))


def _sort_todos(todos: list[Todo]) -> None:
    """Sort todos by time (timed first, untimed last)."""
    todos.sort(key=lambda t: (t.time is None, t.time or ""))


def handle_todo_complete(args) -> None:
    """Handle todo complete command (Issue #45: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        raise TimelineValidationError(f"Todo not found: {args.id}")

    date, record, idx, todo = result
    todo.status = "completed"

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"[{args.id}] Completed: {todo.text}")


def handle_todo_abandon(args) -> None:
    """Handle todo abandon command (Issue #45: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        raise TimelineValidationError(f"Todo not found: {args.id}")

    date, record, idx, todo = result
    todo.status = "abandoned"

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"[{args.id}] Abandoned: {todo.text}")


def handle_todo_edit(args) -> None:
    """Handle todo edit command (Issue #83: TimeExpr for --new-at)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        raise TimelineValidationError(f"Todo not found: {args.id}")

    old_date, record, idx, todo = result

    # Track changes for diff-style output
    changes = []

    # Handle --new-at parameter (Issue #83)
    if args.new_at is not None:
        time_expr = TimeExpr.parse(args.new_at)

        # Determine normalized date and time
        if time_expr.kind == "timerange" and time_expr.timerange.is_undated:
            # Special case: undated (Timerange keyword)
            new_date = None
            new_time = None
        elif time_expr.kind == "timerange":
            # Regular timerange - reject for edit
            raise TimelineValidationError(
                "Cannot use timerange for --new-at in edit command. "
                "Use a timepoint like 'todayT09:00', 'today', 'undated', or 'now'."
            )
        else:
            # Timepoint
            tp = time_expr.timepoint
            if tp.is_undated:
                new_date = None
                new_time = None
            else:
                dt = tp.to_datetime()
                if dt is None:
                    new_date = None
                    new_time = None
                elif isinstance(dt, datetime):
                    new_date = dt.date().isoformat()
                    new_time = dt.strftime("%H:%M")
                else:
                    new_date = dt.isoformat()
                    new_time = None

        # Track date/time changes
        old_time_str = todo.time or "(no time)"
        new_time_str = new_time or "(no time)"

        # If date changed, need to move todo to different record
        if new_date != old_date:
            # Remove from old record
            record.todos.pop(idx)

            # Get or create new record
            new_record = get_or_create_daily_record(timeline, new_date)

            # Update todo's time
            todo.time = new_time

            # Add to new record and sort
            new_record.todos.append(todo)
            _sort_todos(new_record.todos)

            # Track changes
            if old_date is None:
                old_date_str = "undated"
            else:
                old_date_str = old_date

            if new_date is None:
                new_date_str = "undated"
            else:
                new_date_str = new_date

            changes.append(("date", old_date_str, new_date_str))
            if old_time_str != new_time_str:
                changes.append(("time", old_time_str, new_time_str))
        else:
            # Same date, just update time
            if new_time != todo.time:
                todo.time = new_time
                changes.append(("time", old_time_str, new_time_str))
                _sort_todos(record.todos)

    # Apply other edits and track changes
    if args.new_text:
        old_text = todo.text
        todo.text = args.new_text
        changes.append(("text", old_text, args.new_text))

    if args.append_detail:
        # Issue #54: Support multiple --append-detail calls
        for detail in args.append_detail:
            todo.details.append(detail)
            changes.append(("detail", None, detail, "append"))
    if args.set_detail:
        # Issue #54: Parse \n-separated details
        old_details = ", ".join(todo.details) if todo.details else "(no details)"
        new_details = ", ".join([line for line in args.set_detail.split("\n") if line.strip()])
        todo.details = [line for line in args.set_detail.split("\n") if line.strip()]
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


def handle_todo_delete(args) -> None:
    """Handle todo delete command (Issue #45: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        raise TimelineValidationError(f"Todo not found: {args.id}")

    date, record, idx, todo = result

    # Check confirmation (skip with --yes)
    if not args.yes:
        print(f"Delete '{todo.text}'? [y/N]: ")
        response = input().strip().lower()
        if response != "y":
            print("Cancelled")
            return

    # Remove todo
    record.todos.pop(idx)

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"[{args.id}] Deleted: {todo.text}")
