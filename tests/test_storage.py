"""Tests for the storage layer."""

from datetime import date
from pathlib import Path

import pytest

from timeline_cli.errors import TimelineError, TimelineFileNotFoundError, TimelineValidationError
from timeline_cli.models import Event, Note
from timeline_cli.storage import (
    _find_index,
    add_event,
    add_note,
    delete_item,
    edit_event,
    edit_note,
    filter_by_date,
    filter_by_text,
    find_by_id,
    next_id,
    parse_id,
    read_timeline,
    resolve_data_file,
    write_timeline,
)
from timeline_cli.time_expression import DateRange, TimePoint


class TestReadTimeline:
    """Tests for read_timeline()."""

    VALID_HEADER = '{"schema_version": 2}'
    EVENT_LINE = '{"type": "event", "id": 1, "date": "2026-06-26", "time": "14:00", "text": "had a standup"}'
    NOTE_LINE = '{"type": "note", "id": 2, "date": "2026-06-26", "text": "weather is nice today"}'

    def test_reads_valid_file(self, tmp_path: Path) -> None:
        """It parses header + events + notes correctly."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(f"{self.VALID_HEADER}\n{self.EVENT_LINE}\n{self.NOTE_LINE}\n")

        header, items = read_timeline(data_file)

        assert header == {"schema_version": 2}
        assert len(items) == 2
        assert isinstance(items[0], Event)
        assert isinstance(items[1], Note)
        assert items[0].id == 1
        assert items[0].date == "2026-06-26"
        assert items[0].time == "14:00"
        assert items[0].text == "had a standup"
        assert items[1].id == 2
        assert items[1].date == "2026-06-26"
        assert items[1].text == "weather is nice today"

    def test_missing_file(self, tmp_path: Path) -> None:
        """It raises TimelineFileNotFoundError when file does not exist."""
        with pytest.raises(TimelineFileNotFoundError):
            read_timeline(tmp_path / "nonexistent.jsonl")

    def test_empty_file(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError for an empty file."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text("")

        with pytest.raises(TimelineValidationError, match="Empty"):
            read_timeline(data_file)

    def test_missing_schema_version(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError when schema_version is absent."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text('{"foo": "bar"}\n')

        with pytest.raises(TimelineValidationError, match="schema_version"):
            read_timeline(data_file)

    def test_wrong_schema_version(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError for unsupported schema versions."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text('{"schema_version": 1}\n')

        with pytest.raises(TimelineValidationError, match="Unsupported schema version"):
            read_timeline(data_file)

    def test_file_with_only_header(self, tmp_path: Path) -> None:
        """It returns empty items list when file has only a header."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(f"{self.VALID_HEADER}\n")

        header, items = read_timeline(data_file)

        assert header == {"schema_version": 2}
        assert items == []

    def test_file_with_only_header_no_trailing_newline(self, tmp_path: Path) -> None:
        """It works when the header line has no trailing newline."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(self.VALID_HEADER)

        header, items = read_timeline(data_file)

        assert header == {"schema_version": 2}
        assert items == []

    def test_invalid_json_line(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError for unparseable JSON after header."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(f"{self.VALID_HEADER}\nnot valid json\n")

        with pytest.raises(TimelineValidationError, match="Invalid JSON on line 2"):
            read_timeline(data_file)

    def test_invalid_header_json(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError when header is not valid JSON."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text("not json\n")

        with pytest.raises(TimelineValidationError, match="Invalid JSON in header"):
            read_timeline(data_file)

    def test_header_is_not_a_dict(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError when header is valid JSON but not an object."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text("42\n")

        with pytest.raises(TimelineValidationError, match="Header must be a JSON object"):
            read_timeline(data_file)

    def test_unknown_type(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError for unknown type discriminators."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(f'{self.VALID_HEADER}\n{{"type": "todo", "id": 1, "text": "stuff"}}\n')

        with pytest.raises(TimelineValidationError, match="Unknown type 'todo' on line 2"):
            read_timeline(data_file)

    def test_missing_type_field(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError when type field is absent."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(f'{self.VALID_HEADER}\n{{"id": 1, "text": "no type"}}\n')

        with pytest.raises(TimelineValidationError, match="Missing 'type' field on line 2"):
            read_timeline(data_file)

    def test_missing_required_event_field(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError when an event is missing a required field."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(f'{self.VALID_HEADER}\n{{"type": "event", "id": 1, "text": "no date"}}\n')

        with pytest.raises(TimelineValidationError, match="Missing field"):
            read_timeline(data_file)

    def test_missing_required_note_field(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError when a note is missing a required field."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(f'{self.VALID_HEADER}\n{{"type": "note", "id": 1, "date": "2026-06-26"}}\n')

        with pytest.raises(TimelineValidationError, match="Missing field"):
            read_timeline(data_file)

    def test_skips_empty_lines(self, tmp_path: Path) -> None:
        """It tolerates blank lines between data lines."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text(f"{self.VALID_HEADER}\n\n{self.EVENT_LINE}\n\n")

        header, items = read_timeline(data_file)

        assert len(items) == 1
        assert isinstance(items[0], Event)


class TestWriteTimeline:
    """Tests for write_timeline()."""

    def test_writes_header_and_items(self, tmp_path: Path) -> None:
        """It writes a valid JSONL file with header and items."""
        data_file = tmp_path / "data.jsonl"
        header = {"schema_version": 2}
        items = [
            Event(id=1, date="2026-06-26", time="14:00", text="had a standup"),
            Note(id=2, date="2026-06-26", text="weather is nice today"),
        ]

        write_timeline(data_file, header, items)

        content = data_file.read_text()
        assert content == (
            '{"schema_version": 2}\n'
            '{"type": "event", "id": 1, "date": "2026-06-26", "time": "14:00", "text": "had a standup"}\n'
            '{"type": "note", "id": 2, "date": "2026-06-26", "text": "weather is nice today"}\n'
        )

    def test_writes_empty_items(self, tmp_path: Path) -> None:
        """It writes only the header when items list is empty."""
        data_file = tmp_path / "data.jsonl"
        header = {"schema_version": 2}

        write_timeline(data_file, header, [])

        assert data_file.read_text() == '{"schema_version": 2}\n'

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        """It overwrites an existing file completely."""
        data_file = tmp_path / "data.jsonl"
        data_file.write_text('{"schema_version": 2}\n')
        header = {"schema_version": 2}
        items = [Event(id=42, date="2026-06-26", time="10:00", text="new data")]

        write_timeline(data_file, header, items)

        assert data_file.read_text() == (
            '{"schema_version": 2}\n'
            '{"type": "event", "id": 42, "date": "2026-06-26", "time": "10:00", "text": "new data"}\n'
        )

    def test_unicode_round_trip(self, tmp_path: Path) -> None:
        """Emoji, CJK, and special characters survive write → read intact."""
        data_file = tmp_path / "data.jsonl"
        header = {"schema_version": 2}
        items = [
            Event(id=1, date="2026-06-26", time="14:00", text="🎉 launch party"),
            Note(id=2, date="2026-06-26", text="中文笔记\n💡 アイデア — café résumé"),
        ]

        write_timeline(data_file, header, items)
        read_header, read_items = read_timeline(data_file)

        assert read_header == header
        assert read_items == items
        assert read_items[0].text == "🎉 launch party"
        assert read_items[1].text == "中文笔记\n💡 アイデア — café résumé"

    def test_round_trip(self, tmp_path: Path) -> None:
        """A file written by write_timeline is readable by read_timeline."""
        data_file = tmp_path / "data.jsonl"
        header = {"schema_version": 2}
        items = [
            Event(id=1, date="2026-06-26", time="14:00", text="had a standup"),
            Note(id=2, date="2026-06-26", text="weather is nice today"),
        ]

        write_timeline(data_file, header, items)
        read_header, read_items = read_timeline(data_file)

        assert read_header == header
        assert read_items == items

    def test_missing_schema_version_raises(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError when header is missing schema_version."""
        data_file = tmp_path / "data.jsonl"

        with pytest.raises(TimelineValidationError, match="Header must contain schema_version"):
            write_timeline(data_file, {}, [])

    def test_missing_parent_directory_raises(self, tmp_path: Path) -> None:
        """It raises TimelineError when the parent directory does not exist."""
        data_file = tmp_path / "nonexistent" / "data.jsonl"

        with pytest.raises(TimelineError, match="Cannot write"):
            write_timeline(data_file, {"schema_version": 2}, [])


class TestFindById:
    """Tests for find_by_id()."""

    def test_finds_event_by_id(self) -> None:
        """It returns the Event with the given id."""
        items = [
            Event(id=5, date="2026-06-26", time="10:00", text="meeting"),
            Note(id=3, date="2026-06-26", text="ideas"),
        ]
        result = find_by_id(items, "event", 5)
        assert result is not None
        assert isinstance(result, Event)
        assert result.id == 5
        assert result.text == "meeting"

    def test_finds_note_by_id(self) -> None:
        """It returns the Note with the given id."""
        items = [
            Event(id=5, date="2026-06-26", time="10:00", text="meeting"),
            Note(id=3, date="2026-06-26", text="ideas"),
        ]
        result = find_by_id(items, "note", 3)
        assert result is not None
        assert isinstance(result, Note)
        assert result.id == 3
        assert result.text == "ideas"

    def test_returns_none_for_missing_id(self) -> None:
        """It returns None when no item has the given id."""
        items = [Event(id=1, date="2026-06-26", time="10:00", text="x")]
        assert find_by_id(items, "event", 999) is None

    def test_returns_none_for_type_mismatch(self) -> None:
        """It returns None when an id exists but the type does not match."""
        items = [Event(id=5, date="2026-06-26", time="10:00", text="x")]
        # id=5 is an Event, but we search for a Note
        assert find_by_id(items, "note", 5) is None

    def test_finds_by_id_without_type_filter(self) -> None:
        """When type_ is None, it finds by id regardless of item type."""
        items = [
            Event(id=5, date="2026-06-26", time="10:00", text="meeting"),
            Note(id=3, date="2026-06-26", text="ideas"),
        ]
        result = find_by_id(items, None, 3)
        assert result is not None
        assert isinstance(result, Note)
        assert result.id == 3

    def test_empty_list_returns_none(self) -> None:
        """It returns None for an empty items list."""
        assert find_by_id([], "event", 1) is None

    def test_invalid_type_filter_raises(self) -> None:
        """It raises ValueError for an unknown type discriminator."""
        with pytest.raises(ValueError, match="Unknown type filter"):
            find_by_id([], "todo", 1)

        # Also reject the wrong case ("event" not "Event")
        with pytest.raises(ValueError, match="Unknown type filter"):
            find_by_id([], "Event", 5)

    def test_finds_first_match_when_duplicate_ids(self) -> None:
        """It returns the first match when duplicate IDs exist (defensive)."""
        items = [
            Event(id=7, date="2026-06-26", time="09:00", text="first"),
            Event(id=7, date="2026-06-26", time="10:00", text="second"),
        ]
        result = find_by_id(items, "event", 7)
        assert result is not None
        assert result.text == "first"


class TestNextId:
    """Tests for next_id()."""

    def test_empty_items_returns_1(self) -> None:
        """It returns 1 when the items list is empty."""
        assert next_id([]) == 1

    def test_single_item(self) -> None:
        """It returns max + 1 for a single item."""
        items = [Event(id=5, date="2026-06-26", time="10:00", text="x")]
        assert next_id(items) == 6

    def test_mixed_event_and_note_ids(self) -> None:
        """It scans across both Event and Note items for the max id."""
        items = [
            Event(id=7, date="2026-06-26", time="10:00", text="x"),
            Note(id=3, date="2026-06-25", text="y"),
            Event(id=1, date="2026-06-24", time="09:00", text="z"),
        ]
        assert next_id(items) == 8

    def test_zero_id_returns_1(self) -> None:
        """When the only item has id 0, it returns 1."""
        items = [Event(id=0, date="2026-06-26", time="10:00", text="x")]
        assert next_id(items) == 1


# ---------------------------------------------------------------------------
# New storage helpers (issues 109-114)
# ---------------------------------------------------------------------------


class TestParseId:
    """Tests for parse_id()."""

    def test_parses_event_id(self) -> None:
        """It parses 'e42' to 42 for expected_type='event'."""
        assert parse_id("e42", "event") == 42

    def test_parses_note_id(self) -> None:
        """It parses 'n7' to 7 for expected_type='note'."""
        assert parse_id("n7", "note") == 7

    def test_rejects_wrong_prefix_for_event(self) -> None:
        """It raises when a note-prefixed ID is used for an event."""
        with pytest.raises(TimelineValidationError, match="Expected e-prefixed"):
            parse_id("n1", "event")

    def test_rejects_wrong_prefix_for_note(self) -> None:
        """It raises when an event-prefixed ID is used for a note."""
        with pytest.raises(TimelineValidationError, match="Expected n-prefixed"):
            parse_id("e1", "note")

    def test_rejects_invalid_format(self) -> None:
        """It raises for IDs without valid prefixes."""
        with pytest.raises(TimelineValidationError, match="Invalid ID format"):
            parse_id("abc", "event")

    def test_rejects_bare_number(self) -> None:
        """It raises for bare numbers without prefix."""
        with pytest.raises(TimelineValidationError, match="Invalid ID format"):
            parse_id("42", "event")


class TestResolveDataFile:
    """Tests for resolve_data_file()."""

    def test_default_resolves_to_cwd(self, monkeypatch) -> None:
        """It resolves to CWD/.timeline/data.jsonl by default."""
        monkeypatch.chdir("/tmp")
        result = resolve_data_file()
        assert result == Path("/tmp/.timeline/data.jsonl")

    def test_explicit_base_dir(self) -> None:
        """It resolves relative to the given base_dir."""
        result = resolve_data_file(Path("/custom/path"))
        assert result == Path("/custom/path/.timeline/data.jsonl")


class TestFindIndex:
    """Tests for _find_index()."""

    def test_finds_event_index(self) -> None:
        """It returns the list index of the event."""
        items = [
            Event(id=1, date="2026-06-26", time="10:00", text="first"),
            Event(id=5, date="2026-06-26", time="14:00", text="target"),
            Event(id=3, date="2026-06-25", time="09:00", text="third"),
        ]
        assert _find_index(items, "event", 5) == 1

    def test_finds_note_index(self) -> None:
        """It returns the list index of the note."""
        items = [
            Event(id=1, date="2026-06-26", time="10:00", text="event"),
            Note(id=2, date="2026-06-26", text="target"),
        ]
        assert _find_index(items, "note", 2) == 1

    def test_raises_when_not_found(self) -> None:
        """It raises TimelineValidationError when item is not found."""
        items = [Event(id=1, date="2026-06-26", time="10:00", text="x")]
        with pytest.raises(TimelineValidationError, match="Event not found"):
            _find_index(items, "event", 999)


class TestAddEvent:
    """Tests for add_event()."""

    def test_adds_event_to_items(self) -> None:
        """It creates an Event, allocates an ID, and appends to the list."""
        tp = TimePoint.parse("2026-06-26T14:00")
        items: list = []

        event = add_event(items, "had a standup", tp)

        assert event.id == 1
        assert event.date == "2026-06-26"
        assert event.time == "14:00"
        assert event.text == "had a standup"
        assert len(items) == 1
        assert items[0] is event

    def test_increments_id_from_existing(self) -> None:
        """It uses max(existing IDs) + 1."""
        items = [Event(id=7, date="2026-06-26", time="10:00", text="existing")]
        tp = TimePoint.parse("2026-06-26T15:00")

        event = add_event(items, "new event", tp)

        assert event.id == 8

    def test_rejects_missing_time(self) -> None:
        """It raises when TimePoint has no time component."""
        tp = TimePoint.parse("today")
        items: list = []
        with pytest.raises(TimelineValidationError, match="requires a time component"):
            add_event(items, "x", tp)


class TestAddNote:
    """Tests for add_note()."""

    def test_adds_note_to_items(self) -> None:
        """It creates a Note, allocates an ID, and appends to the list."""
        tp = TimePoint.parse("today")
        items: list = []

        note = add_note(items, "weather is nice", tp)

        assert note.id == 1
        assert note.text == "weather is nice"
        assert len(items) == 1
        assert items[0] is note

    def test_increments_id(self) -> None:
        """It uses max(existing IDs) + 1 across events and notes."""
        items = [Event(id=5, date="2026-06-26", time="10:00", text="event")]
        tp = TimePoint.parse("yesterday")

        note = add_note(items, "note text", tp)

        assert note.id == 6

    def test_rejects_time_component(self) -> None:
        """It raises when TimePoint has a time component."""
        tp = TimePoint.parse("now")
        items: list = []
        with pytest.raises(TimelineValidationError, match="time component"):
            add_note(items, "x", tp)


class TestEditEvent:
    """Tests for edit_event()."""

    def test_edits_text_only(self) -> None:
        """It updates only the text, keeping date and time."""
        items = [Event(id=1, date="2026-06-26", time="14:00", text="old text")]
        new_event, old_event = edit_event(items, 1, new_text="new text")
        assert new_event.text == "new text"
        assert new_event.date == "2026-06-26"
        assert new_event.time == "14:00"
        assert old_event.text == "old text"

    def test_edits_timepoint(self) -> None:
        """It updates date and time from a new TimePoint."""
        items = [Event(id=1, date="2026-06-26", time="14:00", text="standup")]
        tp = TimePoint.parse("2026-06-25T10:00")
        new_event, old_event = edit_event(items, 1, new_tp=tp)
        assert new_event.date == "2026-06-25"
        assert new_event.time == "10:00"
        assert old_event.date == "2026-06-26"

    def test_edits_both(self) -> None:
        """It updates both text and timepoint."""
        items = [Event(id=1, date="2026-06-26", time="14:00", text="old")]
        tp = TimePoint.parse("2026-06-25T09:00")
        new_event, old_event = edit_event(items, 1, new_text="new", new_tp=tp)
        assert new_event.text == "new"
        assert new_event.date == "2026-06-25"
        assert new_event.time == "09:00"

    def test_not_found_raises(self) -> None:
        """It raises TimelineValidationError when event is not found."""
        items: list = []
        with pytest.raises(TimelineValidationError, match="Event not found"):
            edit_event(items, 999, new_text="x")


class TestEditNote:
    """Tests for edit_note()."""

    def test_edits_text_only(self) -> None:
        """It updates only the text, keeping the date."""
        items = [Note(id=2, date="2026-06-26", text="old note")]
        new_note, old_note = edit_note(items, 2, new_text="new note")
        assert new_note.text == "new note"
        assert new_note.date == "2026-06-26"
        assert old_note.text == "old note"

    def test_edits_date(self) -> None:
        """It updates the date from a new TimePoint."""
        items = [Note(id=2, date="2026-06-26", text="a note")]
        tp = TimePoint(date=date(2026, 6, 25), time=None)
        new_note, old_note = edit_note(items, 2, new_tp=tp)
        assert new_note.date == "2026-06-25"
        assert old_note.date == "2026-06-26"

    def test_not_found_raises(self) -> None:
        """It raises TimelineValidationError when note is not found."""
        items: list = []
        with pytest.raises(TimelineValidationError, match="Note not found"):
            edit_note(items, 999, new_text="x")


class TestDeleteItem:
    """Tests for delete_item()."""

    def test_deletes_event(self) -> None:
        """It removes and returns the matching event."""
        items = [Event(id=1, date="2026-06-26", time="10:00", text="delete me")]
        deleted = delete_item(items, "event", 1)
        assert deleted.text == "delete me"
        assert len(items) == 0

    def test_deletes_note(self) -> None:
        """It removes and returns the matching note."""
        items = [Note(id=2, date="2026-06-26", text="delete me too")]
        deleted = delete_item(items, "note", 2)
        assert deleted.text == "delete me too"
        assert len(items) == 0

    def test_not_found_raises(self) -> None:
        """It raises TimelineValidationError when item is not found."""
        items: list = []
        with pytest.raises(TimelineValidationError, match="Event not found"):
            delete_item(items, "event", 999)


class TestFilterByDate:
    """Tests for filter_by_date()."""

    def test_filters_by_single_date(self) -> None:
        """It returns items matching a single date range."""
        items = [
            Event(id=1, date="2026-06-26", time="10:00", text="on date"),
            Event(id=2, date="2026-06-25", time="14:00", text="not on date"),
        ]
        dr = DateRange.parse("2026-06-26")
        result = filter_by_date(items, dr)
        assert len(result) == 1
        assert result[0].id == 1

    def test_filters_by_closed_range(self) -> None:
        """It returns items within a closed range."""
        items = [
            Event(id=1, date="2026-06-24", time="10:00", text="early"),
            Event(id=2, date="2026-06-26", time="14:00", text="middle"),
            Event(id=3, date="2026-06-28", time="09:00", text="late"),
        ]
        dr = DateRange.parse("2026-06-25..2026-06-27")
        result = filter_by_date(items, dr)
        assert len(result) == 1
        assert result[0].id == 2

    def test_filters_open_start(self) -> None:
        """It returns items up to the end date."""
        items = [
            Event(id=1, date="2026-06-24", time="10:00", text="early"),
            Event(id=2, date="2026-06-26", time="14:00", text="late"),
        ]
        dr = DateRange.parse("..2026-06-25")
        result = filter_by_date(items, dr)
        assert len(result) == 1
        assert result[0].id == 1

    def test_filters_open_end(self) -> None:
        """It returns items from the start date onward."""
        items = [
            Event(id=1, date="2026-06-24", time="10:00", text="early"),
            Event(id=2, date="2026-06-26", time="14:00", text="late"),
        ]
        dr = DateRange.parse("2026-06-25..")
        result = filter_by_date(items, dr)
        assert len(result) == 1
        assert result[0].id == 2

    def test_unbounded_returns_all(self) -> None:
        """'..' returns all items."""
        items = [Event(id=1, date="2026-06-26", time="10:00", text="x")]
        dr = DateRange.parse("..")
        result = filter_by_date(items, dr)
        assert len(result) == 1


class TestFilterByText:
    """Tests for filter_by_text()."""

    def test_filters_by_substring(self) -> None:
        """It returns items whose text contains the substring."""
        items = [
            Event(id=1, date="2026-06-26", time="10:00", text="fixed a bug"),
            Event(id=2, date="2026-06-26", time="14:00", text="standup"),
        ]
        result = filter_by_text(items, "bug")
        assert len(result) == 1
        assert result[0].id == 1

    def test_case_sensitive(self) -> None:
        """It performs case-sensitive matching."""
        items = [Event(id=1, date="2026-06-26", time="10:00", text="Fixed a BUG")]
        assert len(filter_by_text(items, "bug")) == 0
        assert len(filter_by_text(items, "BUG")) == 1

    def test_no_match_returns_empty(self) -> None:
        """It returns an empty list when nothing matches."""
        items = [Event(id=1, date="2026-06-26", time="10:00", text="nothing")]
        assert filter_by_text(items, "nonexistent") == []
