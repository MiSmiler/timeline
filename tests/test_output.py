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
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))

            # List with --output json (new API)
            result = run_cli(
                ["todo", "list", "--range", "2026-06-16", "--output", "json"],
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
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))

            # List with --output simple (new API)
            result = run_cli(
                ["todo", "list", "--range", "2026-06-16", "--output", "simple"],
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
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))

            # List with --output table (default, new API)
            result = run_cli(
                ["todo", "list", "--range", "2026-06-16", "--output", "table"],
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
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )

            # List with --output json
            result = run_cli(
                ["event", "list", "--range", "2026-06-16", "--output", "json"],
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
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )

            # List with --output simple
            result = run_cli(
                ["event", "list", "--range", "2026-06-16", "--output", "simple"],
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
            run_cli(["todo", "add", "buy groceries", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "buy milk", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "call mom", "--date", "2026-06-16"], cwd=Path(tmpdir))

            # List with --contains buy (new API)
            result = run_cli(
                ["todo", "list", "--range", "2026-06-16", "--contains", "buy"],
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
            run_cli(["todo", "add", "meeting with team", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "call team lead", "--date", "2026-06-17"], cwd=Path(tmpdir))

            # List with --range and --contains (new API)
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
                ["event", "add", "team meeting", "--date", "2026-06-16", "--time", "10:00"],
                cwd=Path(tmpdir),
            )
            run_cli(
                ["event", "add", "lunch", "--date", "2026-06-16", "--time", "14:00"],
                cwd=Path(tmpdir),
            )

            # List with --contains meeting
            result = run_cli(
                ["event", "list", "--range", "2026-06-16", "--contains", "meeting"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "team meeting" in result.stdout
            assert "lunch" not in result.stdout
