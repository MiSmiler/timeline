"""Init command implementation."""

from pathlib import Path

from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Timeline
from timeline_cli.storage import DEFAULT_STORAGE_FILE, TIMELINE_DIR, write_timeline


def handle_init(args) -> None:
    """Initialize .timeline directory structure.

    Creates .timeline/data.jsonl with schema version header.

    Args:
        args: CLI arguments
    """
    timeline_dir = Path(TIMELINE_DIR)
    data_file = Path(DEFAULT_STORAGE_FILE)

    if data_file.exists():
        raise TimelineValidationError(f"Timeline already initialized. {data_file} exists.")

    # Create directory and data file
    timeline_dir.mkdir(exist_ok=True)
    timeline = Timeline(schema_version=1)
    write_timeline(timeline, data_file)
    print(f"Created {data_file}")
