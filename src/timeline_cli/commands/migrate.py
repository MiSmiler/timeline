"""Migrate command implementation."""

import sys

from timeline_cli.storage import DEFAULT_STORAGE_FILE, read_timeline


def handle_migrate(args) -> None:
    """Handle migrate command."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    if timeline.schema_version == args.to:
        print(f"Error: Already at schema version {args.to}", file=sys.stderr)
        sys.exit(1)

    # For now, only support v1 (no migration needed)
    print(f"Migration to version {args.to} not yet implemented")
    sys.exit(1)
