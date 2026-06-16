"""Storage layer for timeline-cli."""

from pathlib import Path
from typing import TYPE_CHECKING

from timeline_cli.models import DailyRecord, Timeline

if TYPE_CHECKING:
    from timeline_cli.models import Event, Todo

DEFAULT_STORAGE_FILE = "timelines.jsonl"


def read_timeline(path: str | Path = DEFAULT_STORAGE_FILE) -> Timeline:
    """Read timeline from jsonline file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Timeline file not found: {path}")

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
