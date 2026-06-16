"""Todo command implementations."""


from timeline_cli.models import Todo
from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
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
