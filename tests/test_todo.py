"""Tests for todo commands (Issue #45 refactored)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestTodoAdd:
    """Tests for todo add command (new API: TEXT --date DATE --time TIME)."""

    def test_todo_add_creates_entry(self):
        """Tracer bullet: timeline-cli todo add creates a todo entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: init the timeline
            run_cli(["init"], cwd=Path(tmpdir))

            # Add a todo (new argument order)
            result = run_cli(["todo", "add", "test task", "--date", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Verify: check the file
            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")

            # Should have header + one daily record
            assert len(content) == 2

            record = json.loads(content[1])
            assert record["date"] == "2026-06-16"
            assert len(record["todos"]) == 1
            assert record["todos"][0]["text"] == "test task"
            assert record["todos"][0]["status"] == "pending"

    def test_todo_add_with_time(self):
        """Todo add with --time parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["time"] == "14:30"

    def test_todo_add_with_detail(self):
        """Todo add with --detail parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "test", "--date", "2026-06-16", "--detail", "extra info"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["details"] == ["extra info"]

    def test_todo_add_multiple_details(self):
        """Todo add with multiple --detail parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                [
                    "todo",
                    "add",
                    "test",
                    "--date",
                    "2026-06-16",
                    "--detail",
                    "line 1",
                    "--detail",
                    "line 2",
                ],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["details"] == ["line 1", "line 2"]

    def test_todo_add_to_existing_date(self):
        """Adding todo to an existing date should append."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 1", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 2", "--date", "2026-06-16"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert len(record["todos"]) == 2


class TestTodoList:
    """Tests for todo list command (new API: --range required)."""

    def test_todo_list_shows_all_pending(self):
        """Tracer bullet: timeline-cli todo list shows pending todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 1", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 2", "--date", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", ".."], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 1" in result.stdout
            assert "task 2" in result.stdout

    def test_todo_list_filter_by_date(self):
        """Todo list --range filters by date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task A", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task B", "--date", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task A" in result.stdout
            assert "task B" not in result.stdout

    def test_todo_list_filter_by_time(self):
        """Todo list --time filters by time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "morning", "--date", "2026-06-16", "--time", "09:00"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "afternoon", "--date", "2026-06-16", "--time", "14:30"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--time", "14:30"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "afternoon" in result.stdout
            assert "morning" not in result.stdout

    def test_todo_list_filter_by_status(self):
        """Todo list --status filters by status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "pending task", "--date", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID and complete it
            import re

            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            run_cli(["todo", "complete", "--id", todo_id], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--status", "completed"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "pending task" in result.stdout

    def test_todo_list_output_json(self):
        """Todo list --output json outputs JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--output", "json"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should be valid JSON
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) > 0

    def test_todo_list_output_simple(self):
        """Todo list --output simple outputs simple text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--output", "simple"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "2026-06-16" in result.stdout
            assert "task" in result.stdout

    def test_todo_list_contains_filter(self):
        """Todo list --contains filters by substring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "write unit tests", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "write docs", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "review code", "--date", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--contains", "write"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "unit tests" in result.stdout
            assert "docs" in result.stdout
            assert "review" not in result.stdout
