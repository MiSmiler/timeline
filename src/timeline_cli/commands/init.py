"""Init command implementation."""

import json
from pathlib import Path

from timeline_cli.errors import TimelineError, TimelineValidationError
from timeline_cli.storage import DEFAULT_STORAGE_FILE, SUPPORTED_SCHEMA_VERSION


def handle_init(args, data_file: Path | None = None) -> None:
    """Initialize .timeline directory structure.

    Creates .timeline/data.jsonl with schema version header.

    Args:
        args: CLI arguments
        data_file: Path to the data file. Uses DEFAULT_STORAGE_FILE if None.
    """
    target = data_file or DEFAULT_STORAGE_FILE

    if target.exists():
        raise TimelineValidationError(f"Timeline already initialized. {target} exists.")

    # Create directory and data file
    try:
        target.parent.mkdir(exist_ok=True)
        header = json.dumps({"schema_version": SUPPORTED_SCHEMA_VERSION}, ensure_ascii=False)
        target.write_text(header + "\n")
    except OSError as exc:
        raise TimelineError(f"Cannot initialize {target}") from exc

    print(f"Created {target}")
