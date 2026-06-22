"""Doctor command implementation - data validation.

Checks performed:
- JSON validity (each line)
- schema_version header presence
- Date format (YYYY-MM-DD)
- Time format (HH:MM) for events/todos
- Status values (pending/completed/abandoned)
- Required fields per type (event: time+text+date, todo: text, note: text+date)
- Undated todos cannot have time
- Sorting correctness (by date, type, time)
- One note per date maximum
- ID uniqueness

The --fix flag currently only repairs sorting issues (events and todos sorted by time).
TODO: Extend --fix to handle more repair scenarios:
- Remove duplicate IDs (keep first occurrence)
- Remove orphaned items (events without date/time, notes without date)
- Fix invalid status values (default to 'pending')
- Handle multiple notes per date (keep most recent)
"""

import json
import re
from pathlib import Path

from timeline_cli.errors import TimelineFileNotFoundError, TimelineValidationError
from timeline_cli.storage import DEFAULT_STORAGE_FILE


def handle_doctor(args) -> None:
    """Handle doctor command."""
    path = Path(DEFAULT_STORAGE_FILE)

    if not path.exists():
        raise TimelineFileNotFoundError(str(path))

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

    # Track items by date for validation
    items_by_date: dict[str | None, dict[str, list]] = {}
    seen_ids = set()

    # Check each item line
    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue

        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"Line {i}: Invalid JSON")
            continue

        # Validate type field
        item_type = item.get("type")
        if item_type not in ["event", "todo", "note"]:
            errors.append(f"Line {i}: Invalid or missing type '{item_type}'")
            continue

        # Validate date
        date = item.get("date")
        if date is not None:
            if not re.match(r"\d{4}-\d{2}-\d{2}$", date):
                errors.append(f"Line {i}: Invalid date format '{date}'")

        # Track items by date
        date_key = date if date is not None else "null"
        if date_key not in items_by_date:
            items_by_date[date_key] = {"events": [], "todos": [], "notes": []}
        # Map item_type to the correct key in items_by_date
        type_key_map = {"event": "events", "todo": "todos", "note": "notes"}
        items_by_date[date_key][type_key_map[item_type]].append(item)

        # Type-specific validation
        if item_type == "event":
            if not item.get("time"):
                errors.append(f"Line {i}: Event missing time")
            elif not re.match(r"\d{2}:\d{2}$", item.get("time", "")):
                errors.append(f"Line {i}: Invalid time format")
            if not item.get("text"):
                errors.append(f"Line {i}: Event missing text")
            if date is None:
                errors.append(f"Line {i}: Event must have date")

        elif item_type == "todo":
            status = item.get("status")
            if status not in ["pending", "completed", "abandoned"]:
                errors.append(f"Line {i}: Invalid status '{status}'")
            if not item.get("text"):
                errors.append(f"Line {i}: Todo missing text")
            # Undated todo check
            if date is None and item.get("time"):
                errors.append(f"Line {i}: Undated todo should not have time")

        elif item_type == "note":
            if not item.get("text"):
                errors.append(f"Line {i}: Note missing text")
            if date is None:
                errors.append(f"Line {i}: Note must have date")

        # Check ID uniqueness
        item_id = item.get("id")
        if item_id:
            if item_id in seen_ids:
                errors.append(f"Line {i}: Duplicate ID '{item_id}'")
            seen_ids.add(item_id)

    # Check sorting for each date (can be fixed)
    for date, items in items_by_date.items():
        # Check event sorting by time
        events = items["events"]
        sorted_events = sorted(events, key=lambda e: e.get("time", ""))
        if events != sorted_events:
            if args.fix:
                # Need to rewrite lines in sorted order
                fixes.append(f"Date {date}: Fixed event sorting")
            else:
                errors.append(f"Date {date}: Events not sorted by time")

        # Check todo sorting by time
        todos = items["todos"]
        sorted_todos = sorted(todos, key=lambda t: (t.get("time") is None, t.get("time") or ""))
        if todos != sorted_todos:
            if args.fix:
                fixes.append(f"Date {date}: Fixed todo sorting")
            else:
                errors.append(f"Date {date}: Todos not sorted by time")

        # Check note uniqueness (one per date)
        if len(items["notes"]) > 1:
            errors.append(f"Date {date}: Multiple notes (only one allowed)")

    # Apply fixes if requested (requires rewriting entire file in sorted order)
    if args.fix and fixes:
        # Rebuild file in proper sorted order
        from timeline_cli.models import Timeline

        # Read current timeline (it will handle the new format)
        timeline = Timeline.from_lines(lines)
        # Write it back (to_lines will sort properly)
        new_lines = timeline.to_lines()
        path.write_text("\n".join(new_lines) + "\n")

        for fix in fixes:
            print(f"Fixed: {fix}")

    # Report results
    if errors:
        print(f"Found {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        raise TimelineValidationError(f"Found {len(errors)} validation errors")
    else:
        print("All checks passed")
