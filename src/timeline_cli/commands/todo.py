"""Todo command implementations."""

import sys

from timeline_cli.models import Todo
from timeline_cli.output_formatter import OutputFormat, filter_by_contains, format_todos
from timeline_cli.range_parser import filter_todos_by_range, parse_range
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    collect_existing_ids,
    ensure_unique_id,
    find_todo_by_prefix,
    get_or_create_daily_record,
    read_timeline,
    write_timeline,
)


def handle_todo_add(args) -> None:
    """Handle todo add command."""
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
    """Handle todo list command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    # Collect todos with their dates
    todos_with_dates = []

    # Use --range if provided
    if hasattr(args, "range") and args.range:
        date_range = parse_range(args.range)
        todos_with_dates = filter_todos_by_range(timeline.records, date_range)

        # Apply additional filters
        if args.time:
            todos_with_dates = [(d, t) for d, t in todos_with_dates if t.time == args.time]
        if args.status:
            todos_with_dates = [(d, t) for d, t in todos_with_dates if t.status == args.status]
        # Use --contains if provided
        if hasattr(args, "contains") and args.contains:
            todos_with_dates = filter_by_contains(todos_with_dates, args.contains)
        # Legacy: use text_prefix if provided
        elif args.text_prefix:
            todos_with_dates = [(d, t) for d, t in todos_with_dates if t.text.startswith(args.text_prefix)]
    else:
        # Legacy filter logic (--date, --overdue, --undated)
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

        # Apply --contains filter if provided
        if hasattr(args, "contains") and args.contains:
            todos_with_dates = filter_by_contains(todos_with_dates, args.contains)

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
    print(format_todos(todos_with_dates, output_format))


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
