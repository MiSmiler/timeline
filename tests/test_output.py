"""Tests for --output and --contains parameters (Issue #44)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestOutputParameter:
    """Tests for --output parameter."""

    def test_todo_list_output_json(self):
        """Todo list --output json should output JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            # List with --output json
            result = run_cli(
                ["todo", "list", "--date", "2026-06-16", "--output", "json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Verify JSON output
            data = json.loads(result.stdout)
            assert len(data) == 1
            assert data[0]["text"] == "task"

    def test_todo_list_output_simple(self):
        """Todo list --output simple should output simple format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            # List with --output simple
            result = run_cli(
                ["todo", "list", "--date", "2026-06-16", "--output", "simple"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "2026-06-16" in result.stdout
            assert "task" in result.stdout

    def test_todo_list_output_table(self):
        """Todo list --output table should output table format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            # List with --output table (default)
            result = run_cli(
                ["todo", "list", "--date", "2026-06-16", "--output", "table"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "Date" in result.stdout or "ID" in result.stdout  # Header

    def test_event_list_output_json(self):
        """Event list --output json should output JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "2026-06-16", "--time", "14:30", "meeting"],
                cwd=Path(tmpdir),
            )

            # List with --output json
            result = run_cli(
                ["event", "list", "2026-06-16", "--output", "json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Verify JSON output
            data = json.loads(result.stdout)
            assert len(data) == 1
            assert data[0]["text"] == "meeting"

    def test_event_list_output_simple(self):
        """Event list --output simple should output simple format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "2026-06-16", "--time", "14:30", "meeting"],
                cwd=Path(tmpdir),
            )

            # List with --output simple
            result = run_cli(
                ["event", "list", "2026-06-16", "--output", "simple"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "14:30" in result.stdout
            assert "meeting" in result.stdout


class TestContainsParameter:
    """Tests for --contains parameter."""

    def test_todo_list_contains_match(self):
        """Todo list --contains should filter by substring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "buy groceries"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "buy milk"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "call mom"], cwd=Path(tmpdir))

            # List with --contains buy
            result = run_cli(
                ["todo", "list", "--date", "2026-06-16", "--contains", "buy"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "groceries" in result.stdout
            assert "milk" in result.stdout
            assert "mom" not in result.stdout

    def test_todo_list_contains_with_range(self):
        """Todo list --contains should work with --range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "meeting with team"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-17", "call team lead"], cwd=Path(tmpdir))

            # List with --range and --contains
            result = run_cli(
                ["todo", "list", "--range", "..", "--contains", "team"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "meeting with team" in result.stdout
            assert "call team lead" in result.stdout

    def test_event_list_contains_match(self):
        """Event list --contains should filter by substring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "2026-06-16", "--time", "10:00", "team meeting"],
                cwd=Path(tmpdir),
            )
            run_cli(
                ["event", "add", "2026-06-16", "--time", "14:00", "lunch"],
                cwd=Path(tmpdir),
            )

            # List with --contains meeting
            result = run_cli(
                ["event", "list", "2026-06-16", "--contains", "meeting"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "team meeting" in result.stdout
            assert "lunch" not in result.stdout


class TestOutputBackwardCompatibility:
    """Tests for backward compatibility with --json and --simple."""

    def test_todo_list_json_still_works(self):
        """Todo list --json should still work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            # List with --json (legacy)
            result = run_cli(
                ["todo", "list", "--date", "2026-06-16", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            data = json.loads(result.stdout)
            assert len(data) == 1

    def test_todo_list_simple_still_works(self):
        """Todo list --simple should still work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            # List with --simple (legacy)
            result = run_cli(
                ["todo", "list", "--date", "2026-06-16", "--simple"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "2026-06-16" in result.stdout

    def test_json_overrides_output(self):
        """--json should override --output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            # List with both --output and --json (--json should win)
            result = run_cli(
                ["todo", "list", "--date", "2026-06-16", "--output", "table", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Should be JSON, not table
            data = json.loads(result.stdout)
            assert len(data) == 1