"""Tests for the formatting module."""

from timeline_cli.formatting import format_items_jsonl, format_items_markdown
from timeline_cli.models import Event, Note


class TestFormatItemsMarkdown:
    """Tests for format_items_markdown()."""

    def test_empty_returns_empty_string(self) -> None:
        """Empty items list returns empty string."""
        assert format_items_markdown([]) == ""

    def test_single_event(self) -> None:
        """A single event is formatted with H1 date heading."""
        items = [Event(id=1, date="2026-06-26", time="14:00", text="fixed a bug")]
        result = format_items_markdown(items)
        assert result == "# 2026-06-26\n- [e1] 14:00 fixed a bug"

    def test_single_note(self) -> None:
        """A single note is formatted without time."""
        items = [Note(id=2, date="2026-06-26", text="weather is nice today")]
        result = format_items_markdown(items)
        assert result == "# 2026-06-26\n- [n2] weather is nice today"

    def test_groups_by_date_descending(self) -> None:
        """Items are grouped by date with H1 headings, dates descending."""
        items = [
            Event(id=1, date="2026-06-25", time="10:00", text="older event"),
            Event(id=2, date="2026-06-26", time="14:00", text="newer event"),
        ]
        result = format_items_markdown(items)
        expected = "# 2026-06-26\n- [e2] 14:00 newer event\n\n# 2026-06-25\n- [e1] 10:00 older event"
        assert result == expected

    def test_sorts_events_by_time_ascending(self) -> None:
        """Events within a date are sorted by time ascending."""
        items = [
            Event(id=1, date="2026-06-26", time="16:30", text="later"),
            Event(id=2, date="2026-06-26", time="14:00", text="earlier"),
        ]
        result = format_items_markdown(items)
        expected = "# 2026-06-26\n- [e2] 14:00 earlier\n- [e1] 16:30 later"
        assert result == expected

    def test_sorts_notes_by_id_ascending(self) -> None:
        """Notes within a date are sorted by id ascending."""
        items = [
            Note(id=5, date="2026-06-26", text="second"),
            Note(id=3, date="2026-06-26", text="first"),
        ]
        result = format_items_markdown(items)
        expected = "# 2026-06-26\n- [n3] first\n- [n5] second"
        assert result == expected

    def test_events_before_notes_within_date(self) -> None:
        """Events are listed before notes within the same date group."""
        items = [
            Note(id=2, date="2026-06-26", text="a note"),
            Event(id=1, date="2026-06-26", time="14:00", text="an event"),
        ]
        result = format_items_markdown(items)
        expected = "# 2026-06-26\n- [e1] 14:00 an event\n- [n2] a note"
        assert result == expected


class TestFormatItemsJsonl:
    """Tests for format_items_jsonl()."""

    def test_empty_returns_empty_string(self) -> None:
        """Empty items list returns empty string."""
        assert format_items_jsonl([]) == ""

    def test_formats_single_event(self) -> None:
        """A single event is formatted as a JSON line."""
        items = [Event(id=1, date="2026-06-26", time="14:00", text="had a standup")]
        result = format_items_jsonl(items)
        expected = '{"type": "event", "id": 1, "date": "2026-06-26", "time": "14:00", "text": "had a standup"}'
        assert result == expected

    def test_formats_single_note(self) -> None:
        """A single note is formatted as a JSON line without time."""
        items = [Note(id=2, date="2026-06-26", text="weather is nice")]
        result = format_items_jsonl(items)
        expected = '{"type": "note", "id": 2, "date": "2026-06-26", "text": "weather is nice"}'
        assert result == expected

    def test_formats_multiple_items(self) -> None:
        """Multiple items are separated by newlines."""
        items = [
            Event(id=1, date="2026-06-26", time="14:00", text="event"),
            Note(id=2, date="2026-06-26", text="note"),
        ]
        result = format_items_jsonl(items)
        lines = result.split("\n")
        assert len(lines) == 2
        assert '"type": "event"' in lines[0]
        assert '"type": "note"' in lines[1]
