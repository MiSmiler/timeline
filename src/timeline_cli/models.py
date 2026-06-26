"""Domain model dataclasses for timeline-cli.

Event and Note are the core data types stored in .timeline/data.jsonl.
Each has to_dict() / from_dict() for JSONL serialization, where the "type"
key is synthetic (not a dataclass field) and used by the storage layer for
dispatch during deserialization.
"""

from dataclasses import dataclass


@dataclass
class Event:
    """A time-anchored event with date and time."""

    id: int
    date: str
    time: str
    text: str

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


@dataclass
class Note:
    """A date-anchored note without a time component."""

    id: int
    date: str
    text: str

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
