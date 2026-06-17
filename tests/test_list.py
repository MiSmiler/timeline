"""Tests for list command (#13)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestListCommand:
    """Tests for list command."""

    def test_list_shows_all_dates(self):
        """Tracer bullet: timeline-cli list shows all dates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-17", "task"], cwd=Path(tmpdir))
            run_cli(["note", "add", "0000-00-00", "inbox note"], cwd=Path(tmpdir))

            result = run_cli(["list"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "2026-06-16" in result.stdout
            assert "2026-06-17" in result.stdout
            assert "0000-00-00" in result.stdout

    def test_list_json_output(self):
        """List --json outputs JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            result = run_cli(["list", "--json"], cwd=Path(tmpdir))
            assert result.returncode == 0

            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert "2026-06-16" in data

    def test_list_empty_file(self):
        """List on empty timeline shows empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["list"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "No dates" in result.stdout or result.stdout.strip() == ""
