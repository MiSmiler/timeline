"""Integration tests for event command handlers."""

import argparse
from unittest.mock import patch

import pytest

from timeline_cli.commands.event import (
    handle_event_add,
    handle_event_delete,
    handle_event_edit,
    handle_event_list,
)
from timeline_cli.errors import TimelineValidationError
from timeline_cli.models import Event, Note


class TestHandleEventAdd:
    """Tests for handle_event_add()."""

    @pytest.fixture
    def empty_timeline(self):
        """Mock data for an empty timeline."""
        return {"schema_version": 2}, [Event(id=5, date="2026-06-26", time="10:00", text="existing")]

    @pytest.fixture
    def args_add_now(self):
        """Mock args for event add --at now."""
        return argparse.Namespace(text="something happened", at="now")

    def test_adds_event_to_empty_timeline(self, empty_timeline, args_add_now, capsys):
        """It creates an event and prints confirmation."""
        header, items = empty_timeline

        with (
            patch("timeline_cli.commands.event.resolve_data_file") as mock_resolve,
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
            patch("timeline_cli.commands.event.write_timeline"),
        ):
            mock_resolve.return_value = "/fake/data.jsonl"
            handle_event_add(args_add_now)

        captured = capsys.readouterr()
        assert "created e" in captured.out


class TestHandleEventList:
    """Tests for handle_event_list()."""

    def test_no_filters_raises(self) -> None:
        """Calling list with no filters raises TimelineValidationError."""
        args = argparse.Namespace(range_=None, with_text=None, json_output=False)
        with patch("timeline_cli.commands.event.resolve_data_file"):
            with pytest.raises(TimelineValidationError, match="At least one filter"):
                handle_event_list(args)

    def test_list_with_range(self, capsys) -> None:
        """event list --range .. lists all events."""
        items = [
            Event(id=1, date="2026-06-26", time="14:00", text="standup"),
            Note(id=2, date="2026-06-26", text="a note"),
        ]
        header = {"schema_version": 2}
        args = argparse.Namespace(range_="..", with_text=None, json_output=False)

        with (
            patch("timeline_cli.commands.event.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
        ):
            handle_event_list(args)

        captured = capsys.readouterr()
        assert "# 2026-06-26" in captured.out
        assert "[e1] 14:00 standup" in captured.out
        # Notes should not appear in event list output
        assert "a note" not in captured.out

    def test_list_json_output(self, capsys) -> None:
        """event list --range .. --json outputs JSONL."""
        items = [Event(id=1, date="2026-06-26", time="14:00", text="standup")]
        header = {"schema_version": 2}
        args = argparse.Namespace(range_="..", with_text=None, json_output=True)

        with (
            patch("timeline_cli.commands.event.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
        ):
            handle_event_list(args)

        captured = capsys.readouterr()
        assert '"type": "event"' in captured.out
        assert "standup" in captured.out

    def test_list_with_text_filter(self, capsys) -> None:
        """event list --with-text filters by text."""
        items = [
            Event(id=1, date="2026-06-26", time="14:00", text="fixed a bug"),
            Event(id=2, date="2026-06-26", time="15:00", text="standup"),
        ]
        header = {"schema_version": 2}
        args = argparse.Namespace(range_=None, with_text="bug", json_output=False)

        with (
            patch("timeline_cli.commands.event.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
        ):
            handle_event_list(args)

        captured = capsys.readouterr()
        assert "fixed a bug" in captured.out
        assert "standup" not in captured.out

    def test_list_empty_result_prints_nothing(self, capsys) -> None:
        """Empty results print nothing."""
        items: list = []
        header = {"schema_version": 2}
        args = argparse.Namespace(range_="..", with_text=None, json_output=False)

        with (
            patch("timeline_cli.commands.event.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
        ):
            handle_event_list(args)

        captured = capsys.readouterr()
        assert captured.out == ""


class TestHandleEventEdit:
    """Tests for handle_event_edit()."""

    def test_no_flags_raises(self) -> None:
        """Calling edit with no flags raises TimelineValidationError."""
        args = argparse.Namespace(id="e1", new_text=None, new_at=None)
        with patch("timeline_cli.commands.event.resolve_data_file"):
            with pytest.raises(TimelineValidationError, match="At least one modification flag"):
                handle_event_edit(args)

    def test_edits_text(self, capsys) -> None:
        """It edits the text and prints the diff."""
        items = [Event(id=1, date="2026-06-26", time="14:00", text="old text")]
        header = {"schema_version": 2}
        args = argparse.Namespace(id="e1", new_text="new text", new_at=None)

        with (
            patch("timeline_cli.commands.event.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
            patch("timeline_cli.commands.event.write_timeline"),
        ):
            handle_event_edit(args)

        captured = capsys.readouterr()
        assert "edited e1" in captured.out
        assert "old text → new text" in captured.out

    def test_nonexistent_id_raises(self) -> None:
        """It raises for nonexistent event ID."""
        items: list = []
        header = {"schema_version": 2}
        args = argparse.Namespace(id="e999", new_text="new", new_at=None)

        with (
            patch("timeline_cli.commands.event.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
        ):
            with pytest.raises(TimelineValidationError, match="Event not found"):
                handle_event_edit(args)


class TestHandleEventDelete:
    """Tests for handle_event_delete()."""

    def test_deletes_event_no_confirm(self, capsys, monkeypatch) -> None:
        """It deletes with --yes flag."""
        items = [Event(id=1, date="2026-06-26", time="14:00", text="delete me")]
        header = {"schema_version": 2}
        args = argparse.Namespace(id="e1", yes=True)

        with (
            patch("timeline_cli.commands.event.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
            patch("timeline_cli.commands.event.write_timeline"),
        ):
            handle_event_delete(args)

        captured = capsys.readouterr()
        assert "deleted e1: delete me" in captured.out

    def test_nonexistent_id_raises(self) -> None:
        """It raises for nonexistent event ID."""
        items: list = []
        header = {"schema_version": 2}
        args = argparse.Namespace(id="e999", yes=True)

        with (
            patch("timeline_cli.commands.event.resolve_data_file", return_value="/fake/data.jsonl"),
            patch("timeline_cli.commands.event.read_timeline", return_value=(header, items)),
        ):
            with pytest.raises(TimelineValidationError, match="Event not found"):
                handle_event_delete(args)
