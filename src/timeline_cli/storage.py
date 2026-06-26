"""Storage layer for timeline-cli.

Reads and writes .timeline/data.jsonl using a JSONL format:
  {"schema_version": 2}
  {"type": "event", "id": 1, "date": "...", "time": "...", "text": "..."}
  {"type": "note", "id": 2, "date": "...", "text": "..."}
"""

import json
from pathlib import Path

from timeline_cli.errors import TimelineFileNotFoundError, TimelineValidationError
from timeline_cli.models import Event, Note

# Storage path constants
TIMELINE_DIR = ".timeline"
DATA_FILE = "data.jsonl"
DEFAULT_STORAGE_FILE = Path(TIMELINE_DIR) / DATA_FILE
SUPPORTED_SCHEMA_VERSION = 2

# Mapping from type discriminator to model class
_TYPE_MAP = {"event": Event, "note": Note}


def read_timeline(path: str | Path) -> tuple[dict, list[Event | Note]]:
    """Read and parse a timeline JSONL file.

    Args:
        path: Path to the data.jsonl file.

    Returns:
        A tuple of (header_dict, items_list).

    Raises:
        TimelineFileNotFoundError: If the file does not exist.
        TimelineValidationError: If the file is empty, has a missing or
            invalid schema_version header, contains unparseable JSON,
            unknown type discriminator, or missing required fields.
    """
    path = Path(path)

    if not path.exists():
        raise TimelineFileNotFoundError(str(path))

    lines = path.read_text(encoding="utf-8").splitlines()

    if not lines:
        raise TimelineValidationError("Empty timeline file: missing schema_version header")

    # Parse header (first line)
    try:
        header = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise TimelineValidationError(f"Invalid JSON in header (line 1): {exc}") from exc

    if "schema_version" not in header:
        raise TimelineValidationError("Missing schema_version in header")
    if header["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        raise TimelineValidationError(f"Unsupported schema version: {header['schema_version']}")

    items: list[Event | Note] = []

    for i, line in enumerate(lines[1:], start=2):
        stripped = line.strip()
        if not stripped:
            continue

        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise TimelineValidationError(f"Invalid JSON on line {i}: {exc}") from exc

        type_name = data.get("type")
        if type_name not in _TYPE_MAP:
            raise TimelineValidationError(f"Unknown type '{type_name}' on line {i}")

        try:
            item = _TYPE_MAP[type_name].from_dict(data)
        except KeyError as exc:
            raise TimelineValidationError(f"Missing field {exc} on line {i}") from exc

        items.append(item)

    return header, items


def write_timeline(path: str | Path, header: dict, items: list[Event | Note]) -> None:
    """Write a timeline JSONL file.

    This is a full-file write (not append). Creates parent directories
    if they do not exist.

    Args:
        path: Path to the data.jsonl file.
        header: Header dict (must contain at least "schema_version").
        items: List of Event and Note objects to serialize.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [json.dumps(header, ensure_ascii=False)]
    for item in items:
        lines.append(json.dumps(item.to_dict(), ensure_ascii=False))

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def find_by_id(items: list[Event | Note], type_: str | None, id_: int) -> Event | Note | None:
    """Find an item by type and id.

    Args:
        items: List of timeline items to search.
        type_: "event", "note", or None to search all items.
        id_: The item id to find.

    Returns:
        The matching item, or None if not found.
    """
    for item in items:
        if type_ is not None:
            if type_ == "event" and not isinstance(item, Event):
                continue
            if type_ == "note" and not isinstance(item, Note):
                continue
        if item.id == id_:
            return item
    return None


def next_id(items: list[Event | Note]) -> int:
    """Compute the next available ID.

    Args:
        items: List of timeline items.

    Returns:
        max(existing IDs) + 1, or 1 if the list is empty.
    """
    if not items:
        return 1
    return max(item.id for item in items) + 1
