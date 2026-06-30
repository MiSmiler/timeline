"""Domain model dataclasses for timeline-cli.

Event and Note are the core data types stored in .timeline/data.jsonl.
Each has to_dict() / from_dict() for JSONL serialization, where the "type"
key is synthetic (not a dataclass field) and used by the storage layer for
dispatch during deserialization.
"""

import re
from dataclasses import dataclass
from datetime import datetime

from timeline_cli.errors import TimelineValidationError
from timeline_cli.time_expression import TimePoint

# YYYY-MM-DD / HH:MM format validators
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}(:\d{2})?$")


def _validate_id(id_: int) -> None:
    if not isinstance(id_, int) or id_ < 0:
        raise ValueError(f"id must be a non-negative int, got {id_!r}")


def _validate_date(date: str) -> None:
    if not isinstance(date, str):
        raise ValueError(f"date must be str, got {type(date).__name__}")
    if not _DATE_RE.match(date):
        raise ValueError(f"date must be YYYY-MM-DD, got {date!r}")


def _validate_time(time: str) -> None:
    if not isinstance(time, str):
        raise ValueError(f"time must be str, got {type(time).__name__}")
    if not _TIME_RE.match(time):
        raise ValueError(f"time must be HH:MM, got {time!r}")


def _validate_text(text: str) -> None:
    if not isinstance(text, str):
        raise ValueError(f"text must be str, got {type(text).__name__}")


def validate_event_timepoint(tp: TimePoint) -> None:
    """Validate a TimePoint for Event creation/edit.

    Raises:
        TimelineValidationError: If the TimePoint has no time component or is in the future.
    """
    if tp.time is None:
        raise TimelineValidationError("Event requires a time component (e.g., todayT14:00 or now)")
    dt = datetime.combine(tp.date, tp.time)
    if dt > datetime.now():
        raise TimelineValidationError(f"Cannot create event in the future: {tp.date.isoformat()} {tp.time.isoformat()}")


def validate_note_timepoint(tp: TimePoint) -> None:
    """Validate a TimePoint for Note creation/edit.

    Raises:
        TimelineValidationError: If the TimePoint has a time component (notes are date-only).
    """
    if tp.time is not None:
        raise TimelineValidationError(f"Note must not have a time component, got {tp.time.isoformat()}")


@dataclass(frozen=True)
class Event:
    """A time-anchored event with date and time."""

    id: int
    date: str
    time: str
    text: str

    def __post_init__(self) -> None:
        _validate_id(self.id)
        _validate_date(self.date)
        _validate_time(self.time)
        _validate_text(self.text)

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for JSONL writing."""
        return {
            "type": "event",
            "id": self.id,
            "date": self.date,
            "time": self.time,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Construct an Event from a dict read from JSONL.

        Uses direct key access so that missing fields raise KeyError,
        which the storage layer catches and wraps in TimelineValidationError.
        """
        return cls(
            id=data["id"],
            date=data["date"],
            time=data["time"],
            text=data["text"],
        )

    @classmethod
    def create(cls, id_: int, text: str, tp: TimePoint) -> "Event":
        """Factory method: create an Event from a TimePoint with business validation.

        Args:
            id_: The event id (caller must allocate via storage.next_id).
            text: The event description text.
            tp: A TimePoint parsed from the --at expression.

        Returns:
            A new Event instance.

        Raises:
            TimelineValidationError: If the TimePoint has no time component or is in the future.
        """
        validate_event_timepoint(tp)
        return cls(
            id=id_,
            date=tp.date.isoformat(),
            time=tp.time.strftime("%H:%M"),
            text=text,
        )


@dataclass(frozen=True)
class Note:
    """A date-anchored note without a time component."""

    id: int
    date: str
    text: str

    def __post_init__(self) -> None:
        _validate_id(self.id)
        _validate_date(self.date)
        _validate_text(self.text)

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for JSONL writing."""
        return {
            "type": "note",
            "id": self.id,
            "date": self.date,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        """Construct a Note from a dict read from JSONL.

        Uses direct key access so that missing fields raise KeyError,
        which the storage layer catches and wraps in TimelineValidationError.
        """
        return cls(
            id=data["id"],
            date=data["date"],
            text=data["text"],
        )

    @classmethod
    def create(cls, id_: int, text: str, tp: TimePoint) -> "Note":
        """Factory method: create a Note from a TimePoint with business validation.

        Args:
            id_: The note id (caller must allocate via storage.next_id).
            text: The note text.
            tp: A TimePoint parsed from the --at expression.

        Returns:
            A new Note instance.

        Raises:
            TimelineValidationError: If the TimePoint has a time component (notes are date-only).
        """
        validate_note_timepoint(tp)
        return cls(
            id=id_,
            date=tp.date.isoformat(),
            text=text,
        )
