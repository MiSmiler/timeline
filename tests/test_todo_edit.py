"""Tests for todo edit commands (#15)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestTodoEdit:
    """Tests for todo edit command."""

    def test_todo_edit_new_text(self):
        """Tracer bullet: timeline-cli todo edit --new-text updates text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "old task"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "edit", "2026-06-16", "old", "--new-text", "new task"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["text"] == "new task"

    def test_todo_edit_new_time(self):
        """Todo edit --new-time updates time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--time", "09:00", "task"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "edit", "2026-06-16", "--time", "09:00", "task", "--new-time", "14:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["time"] == "14:00"

    def test_todo_edit_append_detail(self):
        """Todo edit --append-detail adds detail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "edit", "2026-06-16", "task", "--append-detail", "extra info"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert "extra info" in record["todos"][0]["details"]

    def test_todo_edit_set_detail(self):
        """Todo edit --set-detail replaces all details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--detail", "old", "task"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "edit", "2026-06-16", "task", "--set-detail", "new 1", "--set-detail", "new 2"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["details"] == ["new 1", "new 2"]


class TestTodoMove:
    """Tests for todo move command."""

    def test_todo_move_to_another_date(self):
        """Tracer bullet: timeline-cli todo move relocates todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "move", "2026-06-16", "2026-06-17", "task"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")

            # Check old date has no todos
            record_old = json.loads(content[1])
            assert record_old["date"] == "2026-06-16"
            assert len(record_old["todos"]) == 0

            # Check new date has the todo
            record_new = json.loads(content[2])
            assert record_new["date"] == "2026-06-17"
            assert len(record_new["todos"]) == 1
            assert record_new["todos"][0]["text"] == "task"

    def test_todo_move_with_time(self):
        """Todo move with --time locates specific todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--time", "09:00", "task"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "move", "2026-06-16", "2026-06-17", "--time", "09:00", "task"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0


class TestTodoDelete:
    """Tests for todo delete command."""

    def test_todo_delete_with_confirmation(self):
        """Tracer bullet: timeline-cli todo delete removes todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            # Use --yes to skip confirmation
            result = run_cli(
                ["todo", "delete", "2026-06-16", "task", "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert len(record["todos"]) == 0

    def test_todo_delete_with_time(self):
        """Todo delete with --time locates specific todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--time", "09:00", "task"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "delete", "2026-06-16", "--time", "09:00", "task", "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

    def test_todo_delete_not_found(self):
        """Todo delete fails if todo not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "delete", "2026-06-16", "missing", "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0