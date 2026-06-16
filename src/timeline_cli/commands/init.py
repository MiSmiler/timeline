"""Init command implementation."""

import sys
from pathlib import Path

from timeline_cli.models import Timeline
from timeline_cli.storage import DEFAULT_STORAGE_FILE, write_timeline


def handle_init() -> None:
    """Initialize a new timelines.jsonl file."""
    path = Path(DEFAULT_STORAGE_FILE)

    if path.exists():
        print(f"Error: {DEFAULT_STORAGE_FILE} already exists", file=sys.stderr)
        sys.exit(1)

    # Create empty timeline with schema version 1
    timeline = Timeline(schema_version=1)
    write_timeline(timeline, path)

    print(f"Created {DEFAULT_STORAGE_FILE}")
