"""Tests for todo edit commands (Issue #45 refactored)."""

import json
import re
import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestTodoEdit:
    """Tests for todo edit command (new API: use --id)."""

    def test_todo_edit_new_text(self):
        """Tracer bullet: timeline-cli todo edit --new-text updates text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "old task", "--date", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-text", "new task"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["text"] == "new task"

    def test_todo_edit_new_time(self):
        """Todo edit --new-time updates time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--date", "2026-06-16", "--time", "09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-time", "14:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["time"] == "14:00"

    def test_todo_edit_append_detail(self):
        """Todo edit --append-detail adds detail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--append-detail", "extra info"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert "extra info" in items["todos"][0]["details"]

    def test_todo_edit_set_detail(self):
        """Todo edit --set-detail replaces all details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--date", "2026-06-16", "--detail", "old"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--set-detail", "new 1", "--set-detail", "new 2"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["details"] == ["new 1", "new 2"]


class TestTodoDelete:
    """Tests for todo delete command (new API: use --id)."""

    def test_todo_delete_with_confirmation(self):
        """Tracer bullet: timeline-cli todo delete removes todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            # Use --yes to skip confirmation
            result = run_cli(
                ["todo", "delete", "--id", todo_id, "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["todos"]) == 0

    def test_todo_delete_not_found(self):
        """Todo delete fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "delete", "--id", "t99999", "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0
