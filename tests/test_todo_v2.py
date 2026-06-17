"""Tests for todo command refactoring (Issue #45)."""

import json
import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestTodoAddV2:
    """Tests for todo add with new argument order: TEXT --date DATE --time TIME."""

    def test_todo_add_new_order(self):
        """Todo add should use new argument order: TEXT --date DATE --time TIME."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            # New argument order: TEXT --date DATE
            result = run_cli(
                ["todo", "add", "test task", "--date", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["todos"]) == 1
            assert items["todos"][0]["text"] == "test task"
            assert items["todos"][0]["status"] == "pending"
            assert items["todos"][0]["date"] == "2026-06-16"

    def test_todo_add_with_time(self):
        """Todo add with --time parameter in new order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            # TEXT --date DATE --time TIME
            result = run_cli(
                ["todo", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["time"] == "14:30"

    def test_todo_add_with_detail(self):
        """Todo add with --detail parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "add", "test", "--date", "2026-06-16", "--detail", "extra info"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["details"] == ["extra info"]


class TestTodoListV2:
    """Tests for todo list with --range as required parameter."""

    def test_todo_list_requires_range(self):
        """Todo list should require --range parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 1", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 2", "--date", "2026-06-17"], cwd=Path(tmpdir))

            # Without --range should fail
            result = run_cli(["todo", "list"], cwd=Path(tmpdir))
            assert result.returncode != 0

    def test_todo_list_with_range(self):
        """Todo list with --range parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 1", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 2", "--date", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", ".."], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 1" in result.stdout
            assert "task 2" in result.stdout

    def test_todo_list_with_range_filter(self):
        """Todo list --range should filter by date range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task A", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task B", "--date", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task A" in result.stdout
            assert "task B" not in result.stdout

    def test_todo_list_output_parameter(self):
        """Todo list should support --output parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "list", "--range", "2026-06-16", "--output", "json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert len(data) == 1
            assert data[0]["text"] == "task"


class TestTodoCompleteV2:
    """Tests for todo complete with --id parameter."""

    def test_todo_complete_by_id(self):
        """Todo complete should use --id to locate todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "test task", "--date", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID from output
            output = result.stdout
            # Output format: "Added todo [t7b3k]: test task"
            import re

            match = re.search(r"\[(t[a-z0-9]+)\]", output)
            assert match is not None
            todo_id = match.group(1)

            # Complete by ID
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


class TestTodoAbandonV2:
    """Tests for todo abandon with --id parameter."""

    def test_todo_abandon_by_id(self):
        """Todo abandon should use --id to locate todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "old task", "--date", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            import re

            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            todo_id = match.group(1)

            # Abandon by ID
            result = run_cli(["todo", "abandon", "--id", todo_id], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["status"] == "abandoned"


class TestTodoEditV2:
    """Tests for todo edit with --id parameter."""

    def test_todo_edit_new_text_by_id(self):
        """Todo edit should use --id to locate todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "old task", "--date", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            import re

            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            todo_id = match.group(1)

            # Edit by ID
            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-text", "new task"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["text"] == "new task"

    def test_todo_edit_clear_time(self):
        """Todo edit --clear-time should remove time field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "task", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            import re

            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            todo_id = match.group(1)

            # Clear time
            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--clear-time"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["time"] is None

    def test_todo_edit_output_parameter(self):
        """Todo edit should support --output parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "task", "--date", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            import re

            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            todo_id = match.group(1)

            # Edit with --output json
            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-text", "new task", "--output", "json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output JSON
            data = json.loads(result.stdout)
            assert data["text"] == "new task"


class TestTodoDeleteV2:
    """Tests for todo delete with --id parameter."""

    def test_todo_delete_by_id(self):
        """Todo delete should use --id to locate todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "task to delete", "--date", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            import re

            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            todo_id = match.group(1)

            # Delete by ID with --yes to skip confirmation
            result = run_cli(["todo", "delete", "--id", todo_id, "--yes"], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["todos"]) == 0

    def test_todo_delete_not_found(self):
        """Todo delete fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["todo", "delete", "--id", "t99999", "--yes"], cwd=Path(tmpdir))
            assert result.returncode != 0
