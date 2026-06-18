"""Tests for output format simplification (Issue #51)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestMarkdownOutput:
    """Tests for markdown output format (Issue #51)."""

    def test_todo_list_default_markdown(self):
        """Todo list should default to markdown output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Buy groceries", "--date", "2026-06-18"], cwd=Path(tmpdir))

            # List without --output flag (should be markdown by default)
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Markdown should have date as header
            assert "# 2026-06-18" in result.stdout
            assert "Buy groceries" in result.stdout

    def test_todo_list_markdown_with_time(self):
        """Todo list markdown should show time if present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["todo", "add", "Meeting", "--date", "2026-06-18", "--time", "14:30"],
                cwd=Path(tmpdir),
            )

            # List
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "# 2026-06-18" in result.stdout
            assert "14:30" in result.stdout
            assert "Meeting" in result.stdout

    def test_todo_list_json_flag(self):
        """Todo list --json should output JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 1", "--date", "2026-06-18"], cwd=Path(tmpdir))

            # List with --json flag
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Verify JSON output
            data = json.loads(result.stdout)
            assert len(data) == 1
            assert data[0]["text"] == "Task 1"

    def test_todo_list_markdown_grouped_by_date(self):
        """Todo list markdown should group todos by date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 1", "--date", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 2", "--date", "2026-06-18"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 3", "--date", "2026-06-18"], cwd=Path(tmpdir))

            # List
            result = run_cli(
                ["todo", "list", "--range", ".."],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should have two date headers
            assert "# 2026-06-17" in result.stdout
            assert "# 2026-06-18" in result.stdout
            assert "Task 1" in result.stdout
            assert "Task 2" in result.stdout
            assert "Task 3" in result.stdout

    def test_todo_list_markdown_with_details(self):
        """Todo list markdown should show details indented under item."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["todo", "add", "Buy groceries", "--date", "2026-06-18", "--detail", "Milk", "--detail", "Bread"],
                cwd=Path(tmpdir),
            )

            # List
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "# 2026-06-18" in result.stdout
            assert "Buy groceries" in result.stdout
            # Details should be indented
            assert "  - Milk" in result.stdout
            assert "  - Bread" in result.stdout

    def test_todo_list_markdown_with_show_id(self):
        """Todo list --show-id should show ID in markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task 1", "--date", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            # Extract ID from output: "Added todo [t7b3k]: Task 1"
            todo_id = result.stdout.split("[")[1].split("]")[0]

            # List with --show-id
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18", "--show-id"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "# 2026-06-18" in result.stdout
            # Should show ID in format (t7b3k)
            assert f"({todo_id})" in result.stdout
            assert "Task 1" in result.stdout

    def test_todo_list_markdown_undated(self):
        """Todo list markdown should show undated todos under # Undated header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup - create undated todo (no time)
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Sometime task", "--date", "0000-00-00"], cwd=Path(tmpdir))

            # List with --range ? (undated items)
            result = run_cli(
                ["todo", "list", "--range", "?"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "# Undated" in result.stdout
            assert "Sometime task" in result.stdout


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
