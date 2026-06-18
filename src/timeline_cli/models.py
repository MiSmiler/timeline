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
        """Convert to list of JSON lines for storage.

        Each item (todo/event/note) is stored as one line.
        Items are sorted by (date, type, time) where:
        - date: null (undated) sorts last
        - type: event < todo < note
        - time: null sorts last within same type
        """
        import json

        lines = [json.dumps({"schema_version": self.schema_version}, ensure_ascii=False)]

        # Collect all items with their metadata
        items = []

        for date, record in self.records.items():
            # Add events
            for event in record.events:
                item_dict = {"type": "event", "date": date}
                item_dict.update(event.to_dict())
                items.append(item_dict)

            # Add todos
            for todo in record.todos:
                item_dict = {"type": "todo", "date": date}
                item_dict.update(todo.to_dict())
                items.append(item_dict)

            # Add note (if exists)
            if record.notes is not None:
                items.append(
                    {
                        "type": "note",
                        "date": date,
                        "text": record.notes,
                    }
                )

        # Sort items by (date, type, time)
        def sort_key(item: dict) -> tuple:
            # Type order: event=0, todo=1, note=2
            type_order = {"event": 0, "todo": 1, "note": 2}

            date = item.get("date")
            # null date (undated) sorts last - use max date string
            date_key = date if date is not None else "9999-99-99"

            type_key = type_order.get(item.get("type"), 99)

            time = item.get("time")
            # null time sorts last - use max time string
            time_key = time if time is not None else "99:99"

            return (date_key, type_key, time_key)

        items.sort(key=sort_key)

        # Convert to JSON lines
        for item in items:
            lines.append(json.dumps(item, ensure_ascii=False))

        return lines

    @classmethod
    def from_lines(cls, lines: list[str]) -> "Timeline":
        """Create from list of JSON lines.

        Supports two formats:
        - New format: Each line is one item with 'type' field
        - Old format: Each line is a DailyRecord with 'date' field but no 'type'
        """
        import json

        if not lines:
            raise ValueError("Empty timeline file")

        first = json.loads(lines[0])
        if "schema_version" not in first:
            raise ValueError("Missing schema_version header")

        records: dict[str, DailyRecord] = {}

        for line in lines[1:]:
            if line.strip():
                item = json.loads(line)
                item_type = item.get("type")
                date = item.get("date")

                # Check if this is old format (DailyRecord with events/todos arrays)
                if item_type is None and "events" in item or "todos" in item or "notes" in item:
                    # Old format: convert to new format internally
                    record = DailyRecord.from_dict(item)
                    records[record.date] = record
                    continue

                # New format: one item per line
                # Get or create daily record for this date
                if date not in records:
                    records[date] = DailyRecord(date=date)

                record = records[date]

                if item_type == "event":
                    # Remove type and date fields before creating Event
                    event_data = {k: v for k, v in item.items() if k not in ("type", "date")}
                    record.events.append(Event.from_dict(event_data))

                elif item_type == "todo":
                    # Remove type and date fields before creating Todo
                    todo_data = {k: v for k, v in item.items() if k not in ("type", "date")}
                    record.todos.append(Todo.from_dict(todo_data))

                elif item_type == "note":
                    record.notes = item.get("text")

                else:
                    raise ValueError(f"Unknown item type: {item_type}")

        return cls(schema_version=first["schema_version"], records=records)
