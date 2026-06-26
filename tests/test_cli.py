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
        with pytest.raises(TimelineValidationError, match="Command not implemented yet"):
            _dispatch(args)

    def test_unknown_resource_with_action_includes_action_in_message(self) -> None:
        """_dispatch includes the action name in the error message if present."""
        args = argparse.Namespace(resource="event", action="add")
        with pytest.raises(TimelineValidationError, match="event add"):
            _dispatch(args)
