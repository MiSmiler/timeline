"""Tests for todo commands (#9)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestTodoAdd:
    """Tests for todo add command."""

    def test_todo_add_creates_entry(self):
        """Tracer bullet: timeline-cli todo add creates a todo entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: init the timeline
            run_cli(["init"], cwd=Path(tmpdir))

            # Add a todo
            result = run_cli(["todo", "add", "2026-06-16", "test task"], cwd=Path(tmpdir))
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
                ["todo", "add", "2026-06-16", "--time", "14:30", "meeting"],
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
                ["todo", "add", "2026-06-16", "--detail", "extra info", "test"],
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
                    "2026-06-16",
                    "--detail",
                    "line 1",
                    "--detail",
                    "line 2",
                    "test",
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
            run_cli(["todo", "add", "2026-06-16", "task 1"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task 2"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert len(record["todos"]) == 2


class TestTodoList:
    """Tests for todo list command."""

    def test_todo_list_shows_all_pending(self):
        """Tracer bullet: timeline-cli todo list shows pending todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task 1"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-17", "task 2"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 1" in result.stdout
            assert "task 2" in result.stdout

    def test_todo_list_filter_by_date(self):
        """Todo list --date filters by date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task A"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-17", "task B"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--date", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task A" in result.stdout
            assert "task B" not in result.stdout

    def test_todo_list_filter_by_time(self):
        """Todo list --time filters by time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--time", "09:00", "morning"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--time", "14:30", "afternoon"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--time", "14:30"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "afternoon" in result.stdout
            assert "morning" not in result.stdout

    def test_todo_list_filter_by_status(self):
        """Todo list --status filters by status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "pending task"], cwd=Path(tmpdir))
            # Manually mark one as completed (will implement complete in #14)
            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            record["todos"][0]["status"] = "completed"
            storage_file.write_text(content[0] + "\n" + json.dumps(record) + "\n")

            result = run_cli(["todo", "list", "--status", "completed"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "pending task" in result.stdout

    def test_todo_list_json_output(self):
        """Todo list --json outputs JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--json"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should be valid JSON
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) > 0

    def test_todo_list_simple_output(self):
        """Todo list --simple outputs simple text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--simple"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "2026-06-16" in result.stdout
            assert "task" in result.stdout

    def test_todo_list_text_prefix_filter(self):
        """Todo list with text prefix positional argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "write unit tests"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "write docs"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "review code"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "write"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "unit tests" in result.stdout
            assert "docs" in result.stdout
            assert "review" not in result.stdout
