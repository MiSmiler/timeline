"""Tests for the init command."""

import json
from pathlib import Path

import pytest

from timeline_cli.commands.init import handle_init
from timeline_cli.errors import TimelineValidationError


class TestHandleInit:
    """Tests for handle_init()."""

    def test_creates_directory_and_data_file(self, tmp_path: Path) -> None:
        """It creates .timeline/data.jsonl with the schema version header."""
        data_file = tmp_path / ".timeline" / "data.jsonl"
        args = None  # args is unused by handle_init

        handle_init(args, data_file=data_file)

        assert data_file.exists()
        content = data_file.read_text()
        assert content == '{"schema_version": 2}\n'

    def test_raises_if_already_initialized(self, tmp_path: Path) -> None:
        """It raises TimelineValidationError if the data file already exists."""
        data_file = tmp_path / ".timeline" / "data.jsonl"
        data_file.parent.mkdir()
        data_file.write_text('{"schema_version":2}\n')
        args = None

        with pytest.raises(TimelineValidationError, match="already initialized"):
            handle_init(args, data_file=data_file)

    def test_header_is_valid_json_line(self, tmp_path: Path) -> None:
        """The first line is valid JSON with schema_version == 2."""
        data_file = tmp_path / ".timeline" / "data.jsonl"
        args = None

        handle_init(args, data_file=data_file)

        lines = data_file.read_text().splitlines()
        assert len(lines) == 1
        header = json.loads(lines[0])
        assert header == {"schema_version": 2}

    def test_default_storage_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """When data_file is not given, uses DEFAULT_STORAGE_FILE relative to cwd."""
        monkeypatch.chdir(tmp_path)
        args = None

        handle_init(args)

        expected = tmp_path / ".timeline" / "data.jsonl"
        assert expected.exists()
