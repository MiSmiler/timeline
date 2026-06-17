"""Tests for todo status commands (Issue #45 refactored)."""

import json
import re
import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestTodoComplete:
    """Tests for todo complete command (new API: use --id)."""

    def test_todo_complete_marks_completed(self):
        """Tracer bullet: timeline-cli todo complete marks todo as completed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "write tests", "--date", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(["todo", "complete", "--id", todo_id], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["status"] == "completed"

    def test_todo_complete_not_found(self):
        """Todo complete fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["todo", "complete", "--id", "t99999"], cwd=Path(tmpdir))
            assert result.returncode != 0


class TestTodoAbandon:
    """Tests for todo abandon command (new API: use --id)."""

    def test_todo_abandon_marks_abandoned(self):
        """Tracer bullet: timeline-cli todo abandon marks todo as abandoned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "old task", "--date", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(["todo", "abandon", "--id", todo_id], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["status"] == "abandoned"

    def test_todo_abandon_not_found(self):
        """Todo abandon fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["todo", "abandon", "--id", "t99999"], cwd=Path(tmpdir))
            assert result.returncode != 0
