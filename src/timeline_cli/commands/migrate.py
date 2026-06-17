"""Migrate command implementation."""

import sys

from timeline_cli.storage import (
    DEFAULT_STORAGE_FILE,
    collect_existing_ids,
    ensure_unique_id,
    read_timeline,
    write_timeline,
)


def handle_migrate(args) -> None:
    """Handle migrate command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if timeline.schema_version == args.to:
        print(f"Already at schema version {args.to}")
        return

    if args.to == 2:
        _migrate_to_v2(timeline)
    else:
        print(f"Migration to version {args.to} not yet implemented")
        sys.exit(1)


def _migrate_to_v2(timeline) -> None:
    """Migrate from v1 to v2: assign IDs to all todos and events."""
    # Collect existing IDs
    existing_ids = collect_existing_ids(timeline)

    # Assign IDs to each todo/event without ID
    count = 0
    for record in timeline.records.values():
        for todo in record.todos:
            if todo.id is None:
                todo.id = ensure_unique_id(existing_ids, "t")
                existing_ids.add(todo.id)
                count += 1
        for event in record.events:
            if event.id is None:
                event.id = ensure_unique_id(existing_ids, "e")
                existing_ids.add(event.id)
                count += 1

    # Update schema version
    timeline.schema_version = 2

    # Write back (UTF-8 encoding)
    write_timeline(timeline, DEFAULT_STORAGE_FILE)
    print(f"Migrated {count} items to schema version 2")
