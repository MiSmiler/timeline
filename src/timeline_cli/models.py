"""Data models for timeline-cli."""

from dataclasses import dataclass, field


@dataclass
class Todo:
    """A task to be done, possibly at a specific time."""

    time: str | None  # HH:MM or None for untimed todos
    text: str
    status: str  # pending | completed | abandoned
    details: list[str] = field(default_factory=list)
    id: str | None = None  # Unique identifier, schema v2

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "time": self.time,
            "text": self.text,
            "status": self.status,
            "details": self.details,
        }
        if self.id is not None:
            result["id"] = self.id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Todo":
        """Create from dictionary."""
        return cls(
            time=data.get("time"),
            text=data["text"],
            status=data.get("status", "pending"),
            details=data.get("details", []),
            id=data.get("id"),  # Optional for backward compatibility
        )


@dataclass
class Event:
    """A record of something that happened at a specific time."""

    time: str  # HH:MM
    text: str
    details: list[str] = field(default_factory=list)
    id: str | None = None  # Unique identifier, schema v2

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "time": self.time,
            "text": self.text,
            "details": self.details,
        }
        if self.id is not None:
            result["id"] = self.id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Create from dictionary."""
        return cls(
            time=data["time"],
            text=data["text"],
            details=data.get("details", []),
            id=data.get("id"),  # Optional for backward compatibility
        )


@dataclass
class DailyRecord:
    """A single day's timeline data."""

    date: str  # YYYY-MM-DD or 0000-00-00
    events: list[Event] = field(default_factory=list)
    todos: list[Todo] = field(default_factory=list)
    notes: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date,
            "events": [e.to_dict() for e in self.events],
            "todos": [t.to_dict() for t in self.todos],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DailyRecord":
        """Create from dictionary."""
        return cls(
            date=data["date"],
            events=[Event.from_dict(e) for e in data.get("events", [])],
            todos=[Todo.from_dict(t) for t in data.get("todos", [])],
            notes=data.get("notes"),
        )


@dataclass
class Timeline:
    """The full timeline data structure."""

    schema_version: int
    records: dict[str, DailyRecord] = field(default_factory=dict)

    def to_lines(self) -> list[str]:
        """Convert to list of JSON lines for storage."""
        import json

        lines = [json.dumps({"schema_version": self.schema_version})]
        for record in self.records.values():
            lines.append(json.dumps(record.to_dict()))
        return lines

    @classmethod
    def from_lines(cls, lines: list[str]) -> "Timeline":
        """Create from list of JSON lines."""
        import json

        if not lines:
            raise ValueError("Empty timeline file")

        first = json.loads(lines[0])
        if "schema_version" not in first:
            raise ValueError("Missing schema_version header")

        records = {}
        for line in lines[1:]:
            if line.strip():
                data = json.loads(line)
                record = DailyRecord.from_dict(data)
                records[record.date] = record

        return cls(schema_version=first["schema_version"], records=records)
