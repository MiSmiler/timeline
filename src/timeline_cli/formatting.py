"""Output formatting for list commands.

Markdown output groups items by date under H1 headings, sorted by date
descending.  Within a date, events are sorted by time ascending and notes
by id ascending.  JSONL output emits one JSON line per item.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from itertools import groupby

from timeline_cli.models import Event, Note


def _type_prefix(item: Event | Note) -> str:
    """Return the user-facing type prefix for an item."""
    if isinstance(item, Event):
        return "e"
    return "n"


def _date_key(item: Event | Note) -> str:
    """Return the date string for grouping."""
    return item.date


def _event_sort_key(event: Event) -> str:
    """Sort key for events: time ascending."""
    return event.time


def _note_sort_key(note: Note) -> str:
    """Sort key for notes: id ascending."""
    return str(note.id)


def _render_event(event: Event) -> str:
    """Render a single event as a markdown list item."""
    return f"- [e{event.id}] {event.time} {event.text}"


def _render_note(note: Note) -> str:
    """Render a single note as a markdown list item."""
    return f"- [n{note.id}] {note.text}"


def format_items_markdown(items: Sequence[Event | Note]) -> str:
    """Format items as markdown grouped by date.

    Dates are in descending order.  Within a date:
    - Events are sorted by time ascending.
    - Notes are sorted by id ascending.

    Args:
        items: List of timeline items to format.

    Returns:
        A markdown string, or an empty string if items is empty.
    """
    if not items:
        return ""

    # Group by date
    sorted_items = sorted(items, key=_date_key, reverse=True)
    groups = groupby(sorted_items, key=_date_key)

    lines: list[str] = []
    for date, group_iter in groups:
        group = list(group_iter)
        events = sorted([item for item in group if isinstance(item, Event)], key=_event_sort_key)
        notes = sorted([item for item in group if isinstance(item, Note)], key=_note_sort_key)

        lines.append(f"# {date}")
        for event in events:
            lines.append(_render_event(event))
        for note in notes:
            lines.append(_render_note(note))
        lines.append("")

    # Remove trailing blank line
    if lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def format_items_jsonl(items: Sequence[Event | Note]) -> str:
    """Format items as JSONL (one JSON object per line).

    Args:
        items: List of timeline items to format.

    Returns:
        A JSONL string, or an empty string if items is empty.
    """
    if not items:
        return ""
    return "\n".join(json.dumps(item.to_dict(), ensure_ascii=False) for item in items)
