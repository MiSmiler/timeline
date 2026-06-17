"""Tests for todo status commands (#14)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestTodoComplete:
    """Tests for todo complete command."""

    def test_todo_complete_marks_completed(self):
        """Tracer bullet: timeline-cli todo complete marks todo as completed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "write tests"], cwd=Path(tmpdir))

            result = run_cli(["todo", "complete", "2026-06-16", "write"], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["status"] == "completed"

    def test_todo_complete_with_time(self):
        """Todo complete with --time locates specific todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--time", "09:00", "morning"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--time", "14:00", "afternoon"], cwd=Path(tmpdir))

            result = run_cli(["todo", "complete", "2026-06-16", "--time", "09:00", "morning"], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["status"] == "completed"
            assert record["todos"][1]["status"] == "pending"

    def test_todo_complete_not_found(self):
        """Todo complete fails if todo not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["todo", "complete", "2026-06-16", "nonexistent"], cwd=Path(tmpdir))
            assert result.returncode != 0

    def test_todo_complete_ambiguous(self):
        """Todo complete fails if multiple todos match prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task A"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task B"], cwd=Path(tmpdir))

            result = run_cli(["todo", "complete", "2026-06-16", "task"], cwd=Path(tmpdir))
            assert result.returncode != 0


class TestTodoAbandon:
    """Tests for todo abandon command."""

    def test_todo_abandon_marks_abandoned(self):
        """Tracer bullet: timeline-cli todo abandon marks todo as abandoned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "old task"], cwd=Path(tmpdir))

            result = run_cli(["todo", "abandon", "2026-06-16", "old"], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["status"] == "abandoned"

    def test_todo_abandon_with_time(self):
        """Todo abandon with --time locates specific todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "--time", "10:00", "task"], cwd=Path(tmpdir))

            result = run_cli(["todo", "abandon", "2026-06-16", "--time", "10:00", "task"], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["status"] == "abandoned"

    def test_todo_abandon_not_found(self):
        """Todo abandon fails if todo not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["todo", "abandon", "2026-06-16", "missing"], cwd=Path(tmpdir))
            assert result.returncode != 0
