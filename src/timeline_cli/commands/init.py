"""Init command implementation."""

from pathlib import Path

from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Timeline
from timeline_cli.storage import DEFAULT_STORAGE_FILE, write_timeline


def handle_init() -> None:
    """Initialize a new .timelines.jsonl file."""
    path = Path(DEFAULT_STORAGE_FILE)

    if path.exists():
        raise TimelineValidationError(f"Timeline file already exists: {path}")

    # Create empty timeline with schema version 1
    timeline = Timeline(schema_version=1)
    write_timeline(timeline, path)

    print(f"Created {DEFAULT_STORAGE_FILE}")
