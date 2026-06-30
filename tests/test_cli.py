"""Tests for the CLI entry point."""

import argparse
from unittest.mock import patch

import pytest

from timeline_cli.cli import _build_parser, _dispatch, main
from timeline_cli.errors import TimelineValidationError


class TestBuildParser:
    """Tests for _build_parser()."""

    def test_has_version_flag(self) -> None:
        """Parser includes --version flag (triggers sys.exit(0))."""
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_has_debug_flag(self) -> None:
        """Parser includes --debug flag."""
        parser = _build_parser()
        args = parser.parse_args(["--debug"])
        assert args.debug is True

        args = parser.parse_args([])
        assert args.debug is False

    def test_has_init_subcommand(self) -> None:
        """Parser includes 'init' subcommand."""
        parser = _build_parser()
        args = parser.parse_args(["init"])
        assert args.resource == "init"

    def test_no_args_sets_resource_to_none(self) -> None:
        """Without subcommand, resource is None."""
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.resource is None

    def test_invalid_resource_exits_with_2(self) -> None:
        """An invalid resource triggers argparse error and sys.exit(2)."""
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["nonexistent"])
        assert exc_info.value.code == 2


class TestBuildParserEvent:
    """Parser tests for 'event' subcommands."""

    def test_event_add_requires_at(self) -> None:
        """event add requires --at."""
        parser = _build_parser()
        args = parser.parse_args(["event", "add", "my text", "--at", "now"])
        assert args.resource == "event"
        assert args.action == "add"
        assert args.text == "my text"
        assert args.at == "now"

    def test_event_add_missing_at_exits(self) -> None:
        """event add exits when --at is missing."""
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["event", "add", "my text"])

    def test_event_list_parses_filters(self) -> None:
        """event list accepts --range and --with-text."""
        parser = _build_parser()
        args = parser.parse_args(["event", "list", "--range", "today", "--with-text", "bug"])
        assert args.action == "list"
        assert args.range_ == "today"
        assert args.with_text == "bug"

    def test_event_list_json_flag(self) -> None:
        """event list --json sets json_output."""
        parser = _build_parser()
        args = parser.parse_args(["event", "list", "--range", "..", "--json"])
        assert args.json_output is True

    def test_event_edit_parses_both_flags(self) -> None:
        """event edit accepts --new-text and --new-at."""
        parser = _build_parser()
        args = parser.parse_args(["event", "edit", "e1", "--new-text", "updated", "--new-at", "todayT14:00"])
        assert args.action == "edit"
        assert args.id == "e1"
        assert args.new_text == "updated"
        assert args.new_at == "todayT14:00"

    def test_event_edit_no_flags_parses(self) -> None:
        """event edit without flags parses OK (validation happens in handler)."""
        parser = _build_parser()
        args = parser.parse_args(["event", "edit", "e1"])
        assert args.new_text is None
        assert args.new_at is None

    def test_event_delete_parses_yes_flag(self) -> None:
        """event delete --yes sets the flag."""
        parser = _build_parser()
        args = parser.parse_args(["event", "delete", "e1", "--yes"])
        assert args.action == "delete"
        assert args.id == "e1"
        assert args.yes is True

    def test_event_delete_defaults_no_yes(self) -> None:
        """event delete without --yes defaults to False."""
        parser = _build_parser()
        args = parser.parse_args(["event", "delete", "e1"])
        assert args.yes is False

    def test_event_without_action_sets_action_none(self) -> None:
        """event without an action sets action=None (dispatch will raise)."""
        parser = _build_parser()
        args = parser.parse_args(["event"])
        assert args.resource == "event"
        assert args.action is None


class TestBuildParserNote:
    """Parser tests for 'note' subcommands."""

    def test_note_add_requires_at(self) -> None:
        """note add requires --at."""
        parser = _build_parser()
        args = parser.parse_args(["note", "add", "my note", "--at", "today"])
        assert args.resource == "note"
        assert args.action == "add"
        assert args.text == "my note"
        assert args.at == "today"

    def test_note_list_parses_filters(self) -> None:
        """note list accepts --range and --with-text."""
        parser = _build_parser()
        args = parser.parse_args(["note", "list", "--range", "2026-06-25..2026-06-30"])
        assert args.range_ == "2026-06-25..2026-06-30"

    def test_note_edit_parses_flags(self) -> None:
        """note edit accepts --new-text and --new-at."""
        parser = _build_parser()
        args = parser.parse_args(["note", "edit", "n2", "--new-text", "changed"])
        assert args.id == "n2"
        assert args.new_text == "changed"

    def test_note_delete_parses_yes_flag(self) -> None:
        """note delete --yes sets the flag."""
        parser = _build_parser()
        args = parser.parse_args(["note", "delete", "n1", "--yes"])
        assert args.yes is True


class TestMain:
    """Tests for main()."""

    def test_no_args_prints_help_and_exits_zero(self, capsys: pytest.CaptureFixture) -> None:
        """Without arguments, prints help to stdout and exits with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out

    def test_init_routes_to_handle_init(self, tmp_path) -> None:
        """'init' command routes to handle_init and creates the data file."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            main(["init"])  # Returns None on success (no sys.exit)
            expected = tmp_path / ".timeline" / "data.jsonl"
            assert expected.exists()
        finally:
            os.chdir(original_cwd)

    def test_invalid_resource_exits_with_2(self, capsys: pytest.CaptureFixture) -> None:
        """Argparse catches invalid resources with sys.exit(2) before dispatch."""
        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "invalid choice" in captured.err


class TestDispatch:
    """Tests for _dispatch()."""

    def test_init_dispatches_to_handle_init(self) -> None:
        """_dispatch with resource='init' calls handle_init."""
        args = argparse.Namespace(resource="init")
        with patch("timeline_cli.commands.init.handle_init") as mock_handle:
            _dispatch(args)
            mock_handle.assert_called_once_with(args)

    def test_unknown_resource_raises_validation_error(self) -> None:
        """_dispatch with an unknown resource raises TimelineValidationError."""
        args = argparse.Namespace(resource="unknown", action=None)
        with pytest.raises(TimelineValidationError, match="Unknown resource"):
            _dispatch(args)

    def test_unknown_action_raises_validation_error(self) -> None:
        """_dispatch with a known resource but unknown action raises TimelineValidationError."""
        args = argparse.Namespace(resource="event", action="unknown_action")
        with pytest.raises(TimelineValidationError, match="Command not implemented yet"):
            _dispatch(args)
