"""Integration tests for note command handlers."""

import argparse
from unittest.mock import patch

import pytest

from timeline_cli.commands.note import (
    handle_note_add,
    handle_note_delete,
    handle_note_edit,
    handle_note_list,
)
from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Event, Note


class TestHandleNoteAdd:
    """Tests for handle_note_add()."""

    def test_adds_note(self, capsys) -> None:
        """It creates a note and prints confirmation."""
        header = {"schema_version": 2}
        items = [Event(id=1, date="2026-06-26", time="10:00", text="existing")]
        args = argparse.Namespace(text="weather is nice", at="today")

        with (
            patch("timeline_cli.commands.note.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.note.read_timeline", return_value=(header, items)),
            patch("timeline_cli.commands.note.write_timeline"),
        ):
            handle_note_add(args)

        captured = capsys.readouterr()
        assert "created n" in captured.out
        assert "weather is nice" in captured.out

    def test_rejects_time_component(self) -> None:
        """It raises when --at has a time component."""
        header = {"schema_version": 2}
        items: list = []
        args = argparse.Namespace(text="bad note", at="now")

        with (
            patch("timeline_cli.commands.note.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.note.read_timeline", return_value=(header, items)),
        ):
            with pytest.raises(TimelineValidationError, match="time component"):
                handle_note_add(args)


class TestHandleNoteList:
    """Tests for handle_note_list()."""

    def test_no_filters_raises(self) -> None:
        """Calling list with no filters raises."""
        args = argparse.Namespace(range_=None, with_text=None, json_output=False)
        with patch("timeline_cli.commands.note.resolve_data_file"):
            with pytest.raises(TimelineValidationError, match="At least one filter"):
                handle_note_list(args)

    def test_list_notes_only(self, capsys) -> None:
        """note list shows only notes, not events."""
        items = [
            Event(id=1, date="2026-06-26", time="14:00", text="an event"),
            Note(id=2, date="2026-06-26", text="a note"),
        ]
        header = {"schema_version": 2}
        args = argparse.Namespace(range_="..", with_text=None, json_output=False)

        with (
            patch("timeline_cli.commands.note.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.note.read_timeline", return_value=(header, items)),
        ):
            handle_note_list(args)

        captured = capsys.readouterr()
        assert "a note" in captured.out
        assert "an event" not in captured.out

    def test_list_json_output(self, capsys) -> None:
        """note list --json outputs JSONL."""
        items = [Note(id=2, date="2026-06-26", text="a note")]
        header = {"schema_version": 2}
        args = argparse.Namespace(range_="..", with_text=None, json_output=True)

        with (
            patch("timeline_cli.commands.note.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.note.read_timeline", return_value=(header, items)),
        ):
            handle_note_list(args)

        captured = capsys.readouterr()
        assert '"type": "note"' in captured.out


class TestHandleNoteEdit:
    """Tests for handle_note_edit()."""

    def test_no_flags_raises(self) -> None:
        """Calling edit with no flags raises."""
        args = argparse.Namespace(id="n1", new_text=None, new_at=None)
        with patch("timeline_cli.commands.note.resolve_data_file"):
            with pytest.raises(TimelineValidationError, match="At least one modification flag"):
                handle_note_edit(args)

    def test_edits_text(self, capsys) -> None:
        """It edits the text and prints diff."""
        items = [Note(id=2, date="2026-06-26", text="old note")]
        header = {"schema_version": 2}
        args = argparse.Namespace(id="n2", new_text="new note", new_at=None)

        with (
            patch("timeline_cli.commands.note.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.note.read_timeline", return_value=(header, items)),
            patch("timeline_cli.commands.note.write_timeline"),
        ):
            handle_note_edit(args)

        captured = capsys.readouterr()
        assert "edited n2" in captured.out
        assert "old note → new note" in captured.out

    def test_edits_date(self, capsys) -> None:
        """It edits the date and prints diff."""
        items = [Note(id=2, date="2026-06-26", text="a note")]
        header = {"schema_version": 2}
        args = argparse.Namespace(id="n2", new_text=None, new_at="2026-06-25")

        with (
            patch("timeline_cli.commands.note.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.note.read_timeline", return_value=(header, items)),
            patch("timeline_cli.commands.note.write_timeline"),
        ):
            handle_note_edit(args)

        captured = capsys.readouterr()
        assert "edited n2" in captured.out
        assert "2026-06-26 → 2026-06-25" in captured.out


class TestHandleNoteDelete:
    """Tests for handle_note_delete()."""

    def test_deletes_note(self, capsys) -> None:
        """It deletes with --yes flag."""
        items = [Note(id=2, date="2026-06-26", text="delete me")]
        header = {"schema_version": 2}
        args = argparse.Namespace(id="n2", yes=True)

        with (
            patch("timeline_cli.commands.note.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.note.read_timeline", return_value=(header, items)),
            patch("timeline_cli.commands.note.write_timeline"),
        ):
            handle_note_delete(args)

        captured = capsys.readouterr()
        assert "deleted n2: delete me" in captured.out

    def test_nonexistent_id_raises(self) -> None:
        """It raises for nonexistent note ID."""
        items: list = []
        header = {"schema_version": 2}
        args = argparse.Namespace(id="n999", yes=True)

        with (
            patch("timeline_cli.commands.note.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.note.read_timeline", return_value=(header, items)),
        ):
            with pytest.raises(TimelineValidationError, match="Note not found"):
                handle_note_delete(args)
