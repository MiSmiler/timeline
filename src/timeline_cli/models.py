"""Domain model dataclasses for timeline-cli.

Event and Note are the core data types stored in .timeline/data.jsonl.
Each has to_dict() / from_dict() for JSONL serialization, where the "type"
key is synthetic (not a dataclass field) and used by the storage layer for
dispatch during deserialization.
"""

import re
from dataclasses import dataclass

# YYYY-MM-DD / HH:MM format validators
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


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
