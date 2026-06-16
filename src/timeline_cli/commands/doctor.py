"""Doctor command implementation - data validation."""

import json
import re
import sys
from pathlib import Path

from timeline_cli.storage import DEFAULT_STORAGE_FILE


def handle_doctor(args) -> None:
    """Handle doctor command."""
    path = Path(DEFAULT_STORAGE_FILE)

    if not path.exists():
        print(f"Error: {DEFAULT_STORAGE_FILE} not found", file=sys.stderr)
        sys.exit(1)

    lines = path.read_text().strip().split("\n")

    errors = []
    fixes = []

    # Check header
    try:
        header = json.loads(lines[0])
        if "schema_version" not in header:
            errors.append("Missing schema_version header")
    except json.JSONDecodeError:
        errors.append("Invalid JSON in header line")

    # Track dates for duplicate check
    seen_dates = set()

    # Check each record line
    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"Line {i}: Invalid JSON")
            continue

        # Validate date
        date = record.get("date")
        if not date:
            errors.append(f"Line {i}: Missing date")
            continue

        if not re.match(r"\d{4}-\d{2}-\d{2}$", date) and date != "0000-00-00":
            errors.append(f"Line {i}: Invalid date format '{date}'")

        if date in seen_dates:
            errors.append(f"Line {i}: Duplicate date '{date}'")
        seen_dates.add(date)

        # Validate events
        for j, event in enumerate(record.get("events", [])):
            if not event.get("time"):
                errors.append(f"Line {i}, Event {j}: Missing time")
            elif not re.match(r"\d{2}:\d{2}$", event.get("time", "")):
                errors.append(f"Line {i}, Event {j}: Invalid time format")
            if not event.get("text"):
                errors.append(f"Line {i}, Event {j}: Missing text")

        # Validate todos
        for j, todo in enumerate(record.get("todos", [])):
            status = todo.get("status")
            if status not in ["pending", "completed", "abandoned"]:
                errors.append(f"Line {i}, Todo {j}: Invalid status '{status}'")
            if not todo.get("text"):
                errors.append(f"Line {i}, Todo {j}: Missing text")
            # 0000-00-00 todos should not have time
            if date == "0000-00-00" and todo.get("time"):
                errors.append(f"Line {i}, Todo {j}: Undated todo should not have time")

        # 0000-00-00 constraints
        if date == "0000-00-00":
            if record.get("events"):
                errors.append(f"Line {i}: Undated record should not have events")
            if record.get("notes"):
                errors.append(f"Line {i}: Undated record should not have notes")

        # Check sorting (can be fixed)
        events = record.get("events", [])
        sorted_events = sorted(events, key=lambda e: e.get("time", ""))
        if events != sorted_events:
            if args.fix:
                fixes.append(f"Line {i}: Fixed event sorting")
                record["events"] = sorted_events
                lines[i] = json.dumps(record)
            else:
                errors.append(f"Line {i}: Events not sorted by time")

        todos = record.get("todos", [])
        sorted_todos = sorted(todos, key=lambda t: (t.get("time") is None, t.get("time") or ""))
        if todos != sorted_todos:
            if args.fix:
                fixes.append(f"Line {i}: Fixed todo sorting")
                record["todos"] = sorted_todos
                lines[i] = json.dumps(record)
            else:
                errors.append(f"Line {i}: Todos not sorted by time")

    # Apply fixes if requested
    if args.fix and fixes:
        path.write_text("\n".join(lines) + "\n")
        for fix in fixes:
            print(f"Fixed: {fix}")

    # Report results
    if errors:
        print(f"Found {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("All checks passed")
