"""Storage layer for timeline-cli."""

import random
import string
from pathlib import Path
from typing import TYPE_CHECKING

from timeline_cli.errors import TimelineFileNotFoundError
from timeline_cli.models import DailyRecord, Timeline

if TYPE_CHECKING:
    from timeline_cli.models import Event, Todo

DEFAULT_STORAGE_FILE = ".timelines.jsonl"

# ID configuration
ID_CHARSET = string.ascii_lowercase + string.digits  # a-z0-9
ID_LENGTH = 5


def generate_id(prefix: str) -> str:
    """Generate a random ID with given prefix.

    Args:
        prefix: 't' for todo, 'e' for event

    Returns:
        ID string like 't7b3k' or 'e4x1m'
    """
    random_part = "".join(random.choices(ID_CHARSET, k=ID_LENGTH))
    return f"{prefix}{random_part}"


def ensure_unique_id(existing_ids: set[str], prefix: str) -> str:
    """Generate a unique ID that doesn't conflict with existing IDs.

    Args:
        existing_ids: Set of IDs already in use
        prefix: 't' for todo, 'e' for event

    Returns:
        Unique ID string
    """
    # Try up to 100 times to avoid infinite loop
    for _ in range(100):
        new_id = generate_id(prefix)
        if new_id not in existing_ids:
            return new_id
    # Fallback: use longer ID if all 5-char IDs are taken
    random_part = "".join(random.choices(ID_CHARSET, k=6))
    return f"{prefix}{random_part}"


def collect_existing_ids(timeline: Timeline) -> set[str]:
    """Collect all existing IDs from timeline.

    Args:
        timeline: Timeline object

    Returns:
        Set of all existing IDs
    """
    existing_ids = set()
    for record in timeline.records.values():
        for todo in record.todos:
            if todo.id is not None:
                existing_ids.add(todo.id)
        for event in record.events:
            if event.id is not None:
                existing_ids.add(event.id)
    return existing_ids


def read_timeline(path: str | Path = DEFAULT_STORAGE_FILE) -> Timeline:
    """Read timeline from jsonline file."""
    path = Path(path)
    if not path.exists():
        raise TimelineFileNotFoundError(str(path))

    lines = path.read_text().strip().split("\n")
    return Timeline.from_lines(lines)


def write_timeline(timeline: Timeline, path: str | Path = DEFAULT_STORAGE_FILE) -> None:
    """Write timeline to jsonline file."""
    path = Path(path)
    lines = timeline.to_lines()
    path.write_text("\n".join(lines) + "\n")


def get_or_create_daily_record(timeline: Timeline, date: str) -> DailyRecord:
    """Get existing daily record or create a new one."""
    if date not in timeline.records:
        timeline.records[date] = DailyRecord(date=date)
    return timeline.records[date]


def find_todo_by_prefix(
    record: DailyRecord,
    time: str | None,
    text_prefix: str,
) -> tuple[int, "Todo"] | None:
    """Find todo by date + time (optional) + text prefix.

    Returns tuple of (index, todo) if found, None if not found or ambiguous.
    """
    matches = []
    for i, todo in enumerate(record.todos):
        # Match time if specified
        if time is not None and todo.time != time:
            continue
        # Match text prefix
        if todo.text.startswith(text_prefix):
            matches.append((i, todo))

    if len(matches) == 1:
        return matches[0]
    return None  # Not found or ambiguous


def find_event_by_prefix(
    record: DailyRecord,
    time: str,
    text_prefix: str,
) -> tuple[int, "Event"] | None:
    """Find event by date + time + text prefix.

    Returns tuple of (index, event) if found, None if not found or ambiguous.
    """
    matches = []
    for i, event in enumerate(record.events):
        if event.time != time:
            continue
        if event.text.startswith(text_prefix):
            matches.append((i, event))

    if len(matches) == 1:
        return matches[0]
    return None  # Not found or ambiguous


def find_todo_by_id(record: DailyRecord, todo_id: str) -> tuple[int, "Todo"] | None:
    """Find todo by ID.

    Args:
        record: DailyRecord to search in
        todo_id: Todo ID (e.g., 't7b3k')

    Returns:
        Tuple of (index, todo) if found, None otherwise
    """
    for i, todo in enumerate(record.todos):
        if todo.id == todo_id:
            return (i, todo)
    return None


def find_event_by_id(record: DailyRecord, event_id: str) -> tuple[int, "Event"] | None:
    """Find event by ID.

    Args:
        record: DailyRecord to search in
        event_id: Event ID (e.g., 'e4x1m')

    Returns:
        Tuple of (index, event) if found, None otherwise
    """
    for i, event in enumerate(record.events):
        if event.id == event_id:
            return (i, event)
    return None


def find_todo_by_id_in_timeline(timeline: Timeline, todo_id: str) -> tuple[str, DailyRecord, int, "Todo"] | None:
    """Find todo by ID across all daily records.

    Args:
        timeline: Timeline to search in
        todo_id: Todo ID (e.g., 't7b3k')

    Returns:
        Tuple of (date, record, index, todo) if found, None otherwise
    """
    for date, record in timeline.records.items():
        result = find_todo_by_id(record, todo_id)
        if result is not None:
            index, todo = result
            return (date, record, index, todo)
    return None


def find_event_by_id_in_timeline(timeline: Timeline, event_id: str) -> tuple[str, DailyRecord, int, "Event"] | None:
    """Find event by ID across all daily records.

    Args:
        timeline: Timeline to search in
        event_id: Event ID (e.g., 'e4x1m')

    Returns:
        Tuple of (date, record, index, event) if found, None otherwise
    """
    for date, record in timeline.records.items():
        result = find_event_by_id(record, event_id)
        if result is not None:
            index, event = result
            return (date, record, index, event)
    return None
