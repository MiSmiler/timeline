"""Todo command implementations."""

import sys

from timeline_cli.models import Todo
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    find_todo_by_prefix,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)


def handle_todo_add(args) -> None:
    """Handle todo add command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)
    record = get_or_create_daily_record(timeline, args.date)

    # Create new todo
    todo = Todo(
        time=args.time,
        text=args.text,
        status="pending",
        details=args.detail or [],
    )

    # Add to record and sort by time
    record.todos.append(todo)
    _sort_todos(record.todos)

    # Write back
    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Added todo: {args.text}")


def handle_todo_list(args) -> None:
    """Handle todo list command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Collect todos with their dates
    todos_with_dates = []
    for date, record in timeline.records.items():
        for todo in record.todos:
            # Apply filters
            if args.date and date != args.date:
                continue
            if args.time and todo.time != args.time:
                continue
            if args.status and todo.status != args.status:
                continue
            if args.text_prefix and not todo.text.startswith(args.text_prefix):
                continue

            todos_with_dates.append((date, todo))

    # Output
    if args.json:
        import json

        data = [
            {
                "date": date,
                "time": todo.time,
                "text": todo.text,
                "status": todo.status,
                "details": todo.details,
            }
            for date, todo in todos_with_dates
        ]
        print(json.dumps(data, indent=2))
    elif args.simple:
        for date, todo in todos_with_dates:
            time_str = todo.time or "undated"
            status_str = f"[{todo.status}]"
            print(f"{date} {time_str} {status_str} {todo.text}")
    else:
        # Default table format
        if not todos_with_dates:
            print("No todos found")
            return
        print(f"{'Date':<12} {'Time':<8} {'Status':<10} {'Text'}")
        print("-" * 50)
        for date, todo in todos_with_dates:
            time_str = todo.time or "-"
            print(f"{date:<12} {time_str:<8} {todo.status:<10} {todo.text}")


def _sort_todos(todos: list[Todo]) -> None:
    """Sort todos by time (timed first, untimed last)."""
    todos.sort(key=lambda t: (t.time is None, t.time or ""))


def handle_todo_complete(args) -> None:
    """Handle todo complete command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print(f"Error: No record found for {args.date}", file=sys.stderr)
        sys.exit(1)

    record = timeline.records[args.date]
    result = find_todo_by_prefix(record, args.time, args.text_prefix)

    if result is None:
        print("Error: Todo not found or ambiguous", file=sys.stderr)
        sys.exit(1)

    idx, todo = result
    todo.status = "completed"

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Completed: {todo.text}")


def handle_todo_abandon(args) -> None:
    """Handle todo abandon command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print(f"Error: No record found for {args.date}", file=sys.stderr)
        sys.exit(1)

    record = timeline.records[args.date]
    result = find_todo_by_prefix(record, args.time, args.text_prefix)

    if result is None:
        print("Error: Todo not found or ambiguous", file=sys.stderr)
        sys.exit(1)

    idx, todo = result
    todo.status = "abandoned"

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Abandoned: {todo.text}")


def handle_todo_edit(args) -> None:
    """Handle todo edit command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print(f"Error: No record found for {args.date}", file=sys.stderr)
        sys.exit(1)

    record = timeline.records[args.date]
    result = find_todo_by_prefix(record, args.time, args.text_prefix)

    if result is None:
        print("Error: Todo not found or ambiguous", file=sys.stderr)
        sys.exit(1)

    idx, todo = result

    # Apply edits
    if args.new_text:
        todo.text = args.new_text
    if args.new_time:
        todo.time = args.new_time
    if args.append_detail:
        todo.details.append(args.append_detail)
    if args.set_detail:
        todo.details = args.set_detail

    # Re-sort if time changed
    if args.new_time:
        _sort_todos(record.todos)

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Edited: {todo.text}")


def handle_todo_move(args) -> None:
    """Handle todo move command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.from_date not in timeline.records:
        print(f"Error: No record found for {args.from_date}", file=sys.stderr)
        sys.exit(1)

    from_record = timeline.records[args.from_date]
    result = find_todo_by_prefix(from_record, args.time, args.text_prefix)

    if result is None:
        print("Error: Todo not found or ambiguous", file=sys.stderr)
        sys.exit(1)

    idx, todo = result

    # Remove from old date
    from_record.todos.pop(idx)

    # Add to new date
    to_record = get_or_create_daily_record(timeline, args.to_date)
    to_record.todos.append(todo)
    _sort_todos(to_record.todos)

    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Moved: {todo.text} to {args.to_date}")


def handle_todo_delete(args) -> None:
    """Handle todo delete command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if args.date not in timeline.records:
        print(f"Error: No record found for {args.date}", file=sys.stderr)
        sys.exit(1)

    record = timeline.records[args.date]
    result = find_todo_by_prefix(record, args.time, args.text_prefix)

    if result is None:
        print("Error: Todo not found or ambiguous", file=sys.stderr)
        sys.exit(1)

    idx, todo = result

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
    print(f"Deleted: {todo.text}")
