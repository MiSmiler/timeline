"""Storage layer for timeline-cli.

Reads and writes .timeline/data.jsonl using a JSONL format:
  {"schema_version": 2}
  {"type": "event", "id": 1, "date": "...", "time": "...", "text": "..."}
  {"type": "note", "id": 2, "date": "...", "text": "..."}
"""

import json
import os
from collections.abc import Sequence
from pathlib import Path

from timeline_cli.errors import TimelineError, TimelineFileNotFoundError, TimelineValidationError
from timeline_cli.models import Event, Note

# Storage path constants
TIMELINE_DIR = ".timeline"
DATA_FILE = "data.jsonl"
DEFAULT_STORAGE_FILE = Path(TIMELINE_DIR) / DATA_FILE
SUPPORTED_SCHEMA_VERSION = 2

# Mapping from type discriminator to model class
_TYPE_MAP = {"event": Event, "note": Note}


def read_timeline(path: str | Path) -> tuple[dict, Sequence[Event | Note]]:
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

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        raise TimelineFileNotFoundError(str(path))
    except (OSError, UnicodeDecodeError) as exc:
        raise TimelineError(f"Cannot read {path}") from exc

    if not lines:
        raise TimelineValidationError("Empty timeline file: missing schema_version header")

    # Parse header (first line)
    try:
        header = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise TimelineValidationError("Invalid JSON in header (line 1)") from exc

    if not isinstance(header, dict):
        raise TimelineValidationError("Header must be a JSON object (line 1)")

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
            raise TimelineValidationError(f"Invalid JSON on line {i}") from exc

        type_name = data.get("type")
        if type_name is None:
            raise TimelineValidationError(f"Missing 'type' field on line {i}")
        if type_name not in _TYPE_MAP:
            raise TimelineValidationError(f"Unknown type '{type_name}' on line {i}")

        try:
            item = _TYPE_MAP[type_name].from_dict(data)
        except KeyError as exc:
            raise TimelineValidationError(f"Missing field {exc} on line {i}") from exc

        items.append(item)

    return header, items


def write_timeline(path: str | Path, header: dict, items: Sequence[Event | Note]) -> None:
    """Write a timeline JSONL file.

    This is a full-file write (not append).  The caller must ensure the
    parent directory already exists (use ``timeline-cli init`` first).

    **This function is not safe for concurrent use.**  If two CLI
    invocations call ``write_timeline`` at the same time, one will
    silently overwrite the other, and data can be lost.  The intent is
    that timeline-cli is used interactively by a single human at a time.

    Args:
        path: Path to the data.jsonl file.
        header: Header dict (must contain at least ``"schema_version"``).
        items: List of Event and Note objects to serialize.

    Raises:
        TimelineValidationError: If ``header`` is missing
            ``"schema_version"``.
        TimelineError: If writing fails (permission, disk full, etc.).
    """
    if "schema_version" not in header:
        raise TimelineValidationError("Header must contain schema_version")

    path = Path(path)

    lines = [json.dumps(header, ensure_ascii=False)]
    for item in items:
        lines.append(json.dumps(item.to_dict(), ensure_ascii=False))

    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except (OSError, TypeError) as exc:
        raise TimelineError(f"Cannot write {path}") from exc
    finally:
        tmp.unlink(missing_ok=True)


def find_by_id(items: Sequence[Event | Note], type_: str | None, id_: int) -> Event | Note | None:
    """Find an item by type and id.

    Args:
        items: List of timeline items to search.
        type_: ``"event"``, ``"note"``, or None to search all items.
        id_: The item id to find.

    Returns:
        The matching item, or None if not found.

    Raises:
        ValueError: If ``type_`` is not one of the known type
            discriminators or None.
    """
    if type_ is not None:
        expected_cls = _TYPE_MAP.get(type_)
        if expected_cls is None:
            raise ValueError(f"Unknown type filter: {type_!r}")
        candidates = (item for item in items if isinstance(item, expected_cls))
    else:
        candidates = items

    for item in candidates:
        if item.id == id_:
            return item
    return None


def next_id(items: Sequence[Event | Note]) -> int:
    """Compute the next available ID.

    Args:
        items: List of timeline items.

    Returns:
        max(existing IDs) + 1, or 1 if the list is empty.
    """
    if not items:
        return 1
    return max(item.id for item in items) + 1
