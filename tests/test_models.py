"""Tests for Event and Note dataclasses."""

from datetime import date, time

import pytest

from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Event, Note, validate_event_timepoint, validate_note_timepoint
from timeline_cli.time_expression import TimePoint


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


class TestValidateEventTimepoint:
    """Tests for validate_event_timepoint()."""

    def test_valid_timepoint_passes(self) -> None:
        """A TimePoint with time and not in the future passes validation."""
        tp = TimePoint(date=date(2026, 6, 26), time=time(14, 0))
        # Should not raise
        validate_event_timepoint(tp)

    def test_missing_time_raises(self) -> None:
        """A TimePoint without time raises TimelineValidationError."""
        tp = TimePoint(date=date(2026, 6, 26), time=None)
        with pytest.raises(TimelineValidationError, match="requires a time component"):
            validate_event_timepoint(tp)

    def test_future_datetime_raises(self) -> None:
        """A TimePoint in the future raises TimelineValidationError."""
        tp = TimePoint(date=date(2099, 1, 1), time=time(10, 0))
        with pytest.raises(TimelineValidationError, match="future"):
            validate_event_timepoint(tp)


class TestValidateNoteTimepoint:
    """Tests for validate_note_timepoint()."""

    def test_valid_timepoint_passes(self) -> None:
        """A TimePoint without time passes validation."""
        tp = TimePoint(date=date(2026, 6, 26), time=None)
        # Should not raise
        validate_note_timepoint(tp)

    def test_has_time_raises(self) -> None:
        """A TimePoint with time raises TimelineValidationError."""
        tp = TimePoint(date=date(2026, 6, 26), time=time(14, 0))
        with pytest.raises(TimelineValidationError, match="time component"):
            validate_note_timepoint(tp)


class TestEventCreate:
    """Tests for Event.create()."""

    def test_creates_event_from_valid_timepoint(self) -> None:
        """It creates an Event from a valid TimePoint."""
        tp = TimePoint.parse("2026-06-26T14:00")
        event = Event.create(id_=1, text="had a standup", tp=tp)
        assert event.id == 1
        assert event.date == "2026-06-26"
        assert event.time == "14:00"
        assert event.text == "had a standup"

    def test_rejects_timepoint_without_time(self) -> None:
        """It raises TimelineValidationError when TimePoint has no time."""
        tp = TimePoint.parse("today")
        with pytest.raises(TimelineValidationError, match="requires a time component"):
            Event.create(id_=1, text="x", tp=tp)

    def test_rejects_future_timepoint(self) -> None:
        """It raises TimelineValidationError when TimePoint is in the future."""
        tp = TimePoint.parse("2099-01-01T10:00")
        with pytest.raises(TimelineValidationError, match="future"):
            Event.create(id_=1, text="x", tp=tp)

    def test_creates_event_from_now(self) -> None:
        """It creates an Event from a 'now' TimePoint."""
        tp = TimePoint.parse("now")
        event = Event.create(id_=5, text="something just happened", tp=tp)
        assert event.id == 5
        assert event.text == "something just happened"
        assert event.time is not None


class TestNoteCreate:
    """Tests for Note.create()."""

    def test_creates_note_from_valid_timepoint(self) -> None:
        """It creates a Note from a valid date-only TimePoint."""
        tp = TimePoint(date=date(2026, 6, 26), time=None)
        note = Note.create(id_=2, text="weather is nice", tp=tp)
        assert note.id == 2
        assert note.date == "2026-06-26"
        assert note.text == "weather is nice"

    def test_rejects_timepoint_with_time(self) -> None:
        """It raises TimelineValidationError when TimePoint has time."""
        tp = TimePoint.parse("now")
        with pytest.raises(TimelineValidationError, match="time component"):
            Note.create(id_=2, text="x", tp=tp)

    def test_creates_note_from_today(self) -> None:
        """It creates a Note from a 'today' TimePoint (no time component)."""
        tp = TimePoint.parse("today")
        note = Note.create(id_=3, text="today's note", tp=tp)
        assert note.id == 3
        assert note.text == "today's note"
