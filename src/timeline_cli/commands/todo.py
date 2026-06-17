"""Todo command implementations."""

import sys

from timeline_cli.models import Todo
from timeline_cli.output_formatter import OutputFormat, filter_by_contains, format_todos
from timeline_cli.range_parser import filter_todos_by_range, parse_range
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
    """Handle todo add command (Issue #45: TEXT --date DATE --time TIME)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    record = get_or_create_daily_record(timeline, args.date)

    # Generate unique ID
    existing_ids = collect_existing_ids(timeline)
    todo_id = ensure_unique_id(existing_ids, "t")

    # Create new todo
    todo = Todo(
        time=args.time,
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
    print(f"Added todo [{todo_id}]: {args.text}")


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
    output_format = OutputFormat(args.output)

    # Output
    print(format_todos(todos_with_dates, output_format))


def _sort_todos(todos: list[Todo]) -> None:
    """Sort todos by time (timed first, untimed last)."""
    todos.sort(key=lambda t: (t.time is None, t.time or ""))


def handle_todo_complete(args) -> None:
    """Handle todo complete command (Issue #45: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        print(f"Error: Todo not found with ID '{args.id}'", file=sys.stderr)
        sys.exit(1)

    date, record, idx, todo = result
    todo.status = "completed"

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Completed [{args.id}]: {todo.text}")


def handle_todo_abandon(args) -> None:
    """Handle todo abandon command (Issue #45: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        print(f"Error: Todo not found with ID '{args.id}'", file=sys.stderr)
        sys.exit(1)

    date, record, idx, todo = result
    todo.status = "abandoned"

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Abandoned [{args.id}]: {todo.text}")


def handle_todo_edit(args) -> None:
    """Handle todo edit command (Issue #45: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        print(f"Error: Todo not found with ID '{args.id}'", file=sys.stderr)
        sys.exit(1)

    date, record, idx, todo = result

    # Apply edits
    if args.new_text:
        todo.text = args.new_text
    if args.new_time:
        todo.time = args.new_time
    if args.clear_time:
        todo.time = None
    if args.append_detail:
        todo.details.append(args.append_detail)
    if args.set_detail:
        todo.details = args.set_detail

    # Re-sort if time changed
    if args.new_time or args.clear_time:
        _sort_todos(record.todos)

    write_timeline(timeline, DEFAULT_STORAGE_FILE)

    # Output based on format
    if args.output == "json":
        import json

        output = {
            "id": todo.id,
            "date": date,
            "text": todo.text,
            "time": todo.time,
            "status": todo.status,
            "details": todo.details,
        }
        print(json.dumps(output))
    else:
        print(f"Edited [{args.id}]: {todo.text}")


def handle_todo_delete(args) -> None:
    """Handle todo delete command (Issue #45: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        print(f"Error: Todo not found with ID '{args.id}'", file=sys.stderr)
        sys.exit(1)

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
    print(f"Deleted [{args.id}]: {todo.text}")
