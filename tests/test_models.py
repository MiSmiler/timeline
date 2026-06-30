"""Tests for Event and Note dataclasses."""

import pytest

from timeline_cli.models import Event, Note


class TestEvent:
    """Tests for the Event dataclass."""

    def test_event_fields(self) -> None:
        """All four fields are stored and retrieved correctly."""
        event = Event(id=1, date="2026-06-26", time="14:00", text="had a standup")
        assert event.id == 1
        assert event.date == "2026-06-26"
        assert event.time == "14:00"
        assert event.text == "had a standup"

    def test_event_to_dict(self) -> None:
        """to_dict() returns a dict with type=event and all field values."""
        event = Event(id=1, date="2026-06-26", time="14:00", text="had a standup")
        result = event.to_dict()
        assert result == {
            "type": "event",
            "id": 1,
            "date": "2026-06-26",
            "time": "14:00",
            "text": "had a standup",
        }

    def test_event_from_dict(self) -> None:
        """from_dict() constructs an Event from a dict."""
        data = {"id": 1, "date": "2026-06-26", "time": "14:00", "text": "had a standup"}
        event = Event.from_dict(data)
        assert event.id == 1
        assert event.date == "2026-06-26"
        assert event.time == "14:00"
        assert event.text == "had a standup"

    def test_event_from_dict_missing_id(self) -> None:
        """from_dict() raises KeyError when 'id' is missing."""
        with pytest.raises(KeyError):
            Event.from_dict({"date": "2026-06-26", "time": "14:00", "text": "had a standup"})

    def test_event_from_dict_missing_date(self) -> None:
        """from_dict() raises KeyError when 'date' is missing."""
        with pytest.raises(KeyError):
            Event.from_dict({"id": 1, "time": "14:00", "text": "had a standup"})

    def test_event_from_dict_missing_time(self) -> None:
        """from_dict() raises KeyError when 'time' is missing."""
        with pytest.raises(KeyError):
            Event.from_dict({"id": 1, "date": "2026-06-26", "text": "had a standup"})

    def test_event_from_dict_missing_text(self) -> None:
        """from_dict() raises KeyError when 'text' is missing."""
        with pytest.raises(KeyError):
            Event.from_dict({"id": 1, "date": "2026-06-26", "time": "14:00"})

    def test_event_round_trip(self) -> None:
        """Event.from_dict(event.to_dict()) produces an equal Event."""
        original = Event(id=7, date="2026-06-26", time="09:00", text="morning coffee")
        result = Event.from_dict(original.to_dict())
        assert result == original


class TestNote:
    """Tests for the Note dataclass."""

    def test_note_fields(self) -> None:
        """All three fields are stored and retrieved correctly."""
        note = Note(id=2, date="2026-06-26", text="weather is nice today")
        assert note.id == 2
        assert note.date == "2026-06-26"
        assert note.text == "weather is nice today"

    def test_note_has_no_time_field(self) -> None:
        """Note does not have a time attribute."""
        note = Note(id=2, date="2026-06-26", text="weather is nice")
        assert not hasattr(note, "time")

    def test_note_to_dict(self) -> None:
        """to_dict() returns a dict with type=note and all field values."""
        note = Note(id=2, date="2026-06-26", text="weather is nice today")
        result = note.to_dict()
        assert result == {
            "type": "note",
            "id": 2,
            "date": "2026-06-26",
            "text": "weather is nice today",
        }

    def test_note_to_dict_no_time_key(self) -> None:
        """to_dict() does not include a time key."""
        note = Note(id=2, date="2026-06-26", text="weather is nice")
        assert "time" not in note.to_dict()

    def test_note_from_dict(self) -> None:
        """from_dict() constructs a Note from a dict."""
        data = {"id": 2, "date": "2026-06-26", "text": "weather is nice today"}
        note = Note.from_dict(data)
        assert note.id == 2
        assert note.date == "2026-06-26"
        assert note.text == "weather is nice today"

    def test_note_from_dict_missing_id(self) -> None:
        """from_dict() raises KeyError when 'id' is missing."""
        with pytest.raises(KeyError):
            Note.from_dict({"date": "2026-06-26", "text": "weather is nice"})

    def test_note_from_dict_missing_date(self) -> None:
        """from_dict() raises KeyError when 'date' is missing."""
        with pytest.raises(KeyError):
            Note.from_dict({"id": 2, "text": "weather is nice"})

    def test_note_from_dict_missing_text(self) -> None:
        """from_dict() raises KeyError when 'text' is missing."""
        with pytest.raises(KeyError):
            Note.from_dict({"id": 2, "date": "2026-06-26"})

    def test_note_round_trip(self) -> None:
        """Note.from_dict(note.to_dict()) produces an equal Note."""
        original = Note(id=3, date="2026-06-25", text="finished reading")
        result = Note.from_dict(original.to_dict())
        assert result == original
