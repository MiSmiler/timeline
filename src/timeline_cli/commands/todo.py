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

    # Git-style output: [id] Added: text (date time) or [id] Added: text (date)
    if args.time:
        print(f"[{todo_id}] Added: {args.text} ({args.date} {args.time})")
    else:
        print(f"[{todo_id}] Added: {args.text} ({args.date})")


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
    print(f"[{args.id}] Completed: {todo.text}")


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
    print(f"[{args.id}] Abandoned: {todo.text}")


def handle_todo_edit(args) -> None:
    """Handle todo edit command (Issue #45: use --id)."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    result = find_todo_by_id_in_timeline(timeline, args.id)

    if result is None:
        print(f"Error: Todo not found with ID '{args.id}'", file=sys.stderr)
        sys.exit(1)

    date, record, idx, todo = result

    # Track changes for diff-style output
    changes = []

    # Apply edits and track changes
    if args.new_text:
        old_text = todo.text
        todo.text = args.new_text
        changes.append(("text", old_text, args.new_text))

    if args.new_time:
        old_time = todo.time or "(no time)"
        todo.time = args.new_time
        changes.append(("time", old_time, args.new_time))

    if args.clear_time:
        old_time = todo.time or "(no time)"
        todo.time = None
        changes.append(("time", old_time, "(cleared)"))

    if args.append_detail:
        todo.details.append(args.append_detail)
        changes.append(("detail", None, args.append_detail, "append"))

    if args.set_detail:
        old_details = ", ".join(todo.details) if todo.details else "(no details)"
        new_details = ", ".join(args.set_detail)
        todo.details = args.set_detail
        changes.append(("details", old_details, new_details))

    # Re-sort if time changed
    if args.new_time or args.clear_time:
        _sort_todos(record.todos)

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
    print(f"[{args.id}] Deleted: {todo.text}")
