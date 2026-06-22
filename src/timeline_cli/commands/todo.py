"""Todo command implementations."""

import sys

from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Todo
from timeline_cli.output_formatter import OutputFormat, filter_by_contains, format_todos
from timeline_cli.range_parser import (
    filter_todos_by_range,
    parse_at_parameter,
    parse_range,
)
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    collect_existing_ids,
    ensure_unique_id,
    find_todo_by_id_in_timeline,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)


def handle_todo_add(args) -> None:
    """Handle todo add command (Issue #70: TEXT --at AT)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Parse --at parameter
    at_param = parse_at_parameter(args.at)

    # Determine normalized date and time
    normalized_date = at_param.date if at_param.date else "0000-00-00"
    normalized_time = at_param.time

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

    # Git-style output with normalized date and time (Issue #68, #70)
    if normalized_date == "0000-00-00":
        print(f"[{todo_id}] Added: {args.text} (undated)")
    elif normalized_time:
        print(f"[{todo_id}] Added: {args.text} ({normalized_date} {normalized_time})")
    else:
        print(f"[{todo_id}] Added: {args.text} ({normalized_date} no-time)")


def handle_todo_list(args) -> None:
    """Handle todo list command (Issue #45: --range required)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Use --range (now required)
    date_range = parse_range(args.range)
    todos_with_dates = filter_todos_by_range(timeline.records, date_range)

    # Apply additional filters
    if args.time:
        todos_with_dates = [(d, t) for d, t in todos_with_dates if t.time == args.time]
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
    """Handle todo edit command (Issue #70: use --id, --new-at)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        raise TimelineValidationError(f"Todo not found: {args.id}")

    old_date, record, idx, todo = result

    # Track changes for diff-style output
    changes = []

    # Handle --new-at parameter (Issue #70)
    # Note: args.new_at can be "" (empty string) for undated conversion
    if args.new_at is not None:
        at_param = parse_at_parameter(args.new_at)
        new_date = at_param.date if at_param.date else "0000-00-00"
        new_time = at_param.time

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
            if old_date == "0000-00-00":
                old_date_str = "undated"
            else:
                old_date_str = old_date

            if new_date == "0000-00-00":
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
