"""Init command implementation."""

import json
from pathlib import Path

from timeline_cli.errors import TimelineValidationError

# Storage constants
TIMELINE_DIR = ".timeline"
DATA_FILE = "data.jsonl"
DEFAULT_STORAGE_FILE = Path(TIMELINE_DIR) / DATA_FILE


def handle_init(args) -> None:
    """Initialize .timeline directory structure.

    Creates .timeline/data.jsonl with schema version header.

    Args:
        args: CLI arguments
    """
    data_file = Path(DEFAULT_STORAGE_FILE)

    if data_file.exists():
        raise TimelineValidationError(f"Timeline already initialized. {data_file} exists.")

    # Create directory and data file
    data_file.parent.mkdir(exist_ok=True)
    header = json.dumps({"schema_version": 2}, ensure_ascii=False)
    data_file.write_text(header + "\n")
    print(f"Created {data_file}")
