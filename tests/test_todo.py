"""Tests for todo commands (Issue #45 refactored, Issue #70: --at parameter)."""

import json
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestTodoAdd:
    """Tests for todo add command (Issue #70: --at parameter)."""

    def test_todo_add_creates_entry(self):
        """Tracer bullet: timeline-cli todo add creates a todo entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: init the timeline
            run_cli(["init"], cwd=Path(tmpdir))

            # Add a todo with --at parameter
            result = run_cli(["todo", "add", "test task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Verify: check the file
            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            content = storage_file.read_text().strip().split("\n")

            # Should have header + one todo item
            assert len(content) == 2

            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["todos"]) == 1
            assert items["todos"][0]["text"] == "test task"
            assert items["todos"][0]["status"] == "pending"

    def test_todo_add_with_time(self):
        """Todo add with --at parameter including time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "meeting", "--at", "2026-06-16 14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["time"] == "14:30"

    def test_todo_add_with_detail(self):
        """Todo add with --detail parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "test", "--at", "2026-06-16", "--detail", "extra info"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["details"] == ["extra info"]

    def test_todo_add_multiple_details(self):
        """Todo add with multiple --detail parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                [
                    "todo",
                    "add",
                    "test",
                    "--at",
                    "2026-06-16",
                    "--detail",
                    "line 1",
                    "--detail",
                    "line 2",
                ],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["details"] == ["line 1", "line 2"]

    def test_todo_add_to_existing_date(self):
        """Adding todo to an existing date should append."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 1", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 2", "--at", "2026-06-16"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["todos"]) == 2

    def test_todo_add_output_format(self):
        """Todo add outputs git-style format: [id] Added: text (date time)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Review PR", "--at", "2026-06-18 15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [tXXXXX] Added: Review PR (2026-06-18 15:00)
            assert "[t" in result.stdout
            assert "] Added: Review PR (2026-06-18 15:00)" in result.stdout

    def test_todo_add_output_format_no_time(self):
        """Todo add outputs git-style format without time: [id] Added: text (date no-time)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Write tests", "--at", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Issue #68: Should output: [tXXXXX] Added: Write tests (2026-06-18 no-time)
            assert "[t" in result.stdout
            assert "] Added: Write tests (2026-06-18 no-time)" in result.stdout


class TestTodoAddAtParameter:
    """Tests for Issue #70: --at parameter support."""

    def test_todo_add_at_explicit_datetime(self):
        """--at "YYYY-MM-DD HH:MM" works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "2026-06-22 15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "] Added: Task (2026-06-22 15:00)" in result.stdout

    def test_todo_add_at_explicit_date_only(self):
        """--at "YYYY-MM-DD" creates date-only todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "2026-06-22"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "] Added: Task (2026-06-22 no-time)" in result.stdout

    def test_todo_add_at_relative_date(self):
        """--at "today" resolves to today's date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "today"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            today_str = date.today().isoformat()
            assert re.search(r"\[t[a-z0-9]+\] Added: Task \(" + today_str + r" no-time\)", result.stdout)

    def test_todo_add_at_relative_date_with_time(self):
        """--at "today 15:00" resolves date and time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "today 15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            today_str = date.today().isoformat()
            assert re.search(r"\[t[a-z0-9]+\] Added: Task \(" + today_str + r" 15:00\)", result.stdout)

    def test_todo_add_at_time_only_defaults_today(self):
        """--at "15:00" defaults to today."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            today_str = date.today().isoformat()
            assert re.search(r"\[t[a-z0-9]+\] Added: Task \(" + today_str + r" 15:00\)", result.stdout)

    def test_todo_add_at_now(self):
        """--at "now" resolves to current datetime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "now"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            today_str = date.today().isoformat()
            assert re.search(r"\[t[a-z0-9]+\] Added: Task \(" + today_str + r" \d{2}:\d{2}\)", result.stdout)

    def test_todo_add_at_offset(self):
        """--at "-30m" resolves to now - 30m (may cross date boundary)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "-30m"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Output will show the actual date (may be today or yesterday)
            assert re.search(r"\[t[a-z0-9]+\] Added: Task \(\d{4}-\d{2}-\d{2} \d{2}:\d{2}\)", result.stdout)

    def test_todo_add_at_undated(self):
        """--at "" creates undated todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", ""],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "] Added: Task (undated)" in result.stdout

    def test_todo_add_at_required(self):
        """todo add requires --at parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0
            assert "--at" in result.stderr


class TestTodoAddOutputNormalization:
    """Tests for Issue #68: add command output shows normalized date."""

    def test_todo_add_at_today_shows_explicit_date(self):
        """todo add --at today outputs YYYY-MM-DD, not 'today'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "today"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should show YYYY-MM-DD format, not 'today'
            today_str = date.today().isoformat()
            # Pattern: [txxxx] Added: Task (YYYY-MM-DD no-time)
            assert re.search(r"\[t[a-z0-9]+\] Added: Task \(" + today_str + r" no-time\)", result.stdout)

    def test_todo_add_at_yesterday_shows_explicit_date(self):
        """todo add --at yesterday outputs actual date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--at", "yesterday"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            yesterday_str = (date.today() - timedelta(days=1)).isoformat()
            assert re.search(r"\[t[a-z0-9]+\] Added: Task \(" + yesterday_str + r" no-time\)", result.stdout)

    def test_todo_add_at_question_shows_undated(self):
        """todo add --at "" outputs (undated)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Someday task", "--at", ""],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Issue #68: Should output (undated)
            assert "[t" in result.stdout
            assert "] Added: Someday task (undated)" in result.stdout


class TestDateNowRejected:
    """Tests for Issue #69: 'now' is handled by --at, not --date."""

    # Note: --date no longer exists, so these tests are no longer applicable
    # --at "now" is now valid and resolves to current datetime
    # The rejection of --date now was the old behavior before --at


class TestTodoList:
    """Tests for todo list command (new API: --range required)."""

    def test_todo_list_shows_all_pending(self):
        """Tracer bullet: timeline-cli todo list shows pending todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 1", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 2", "--at", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", ".."], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 1" in result.stdout
            assert "task 2" in result.stdout

    def test_todo_list_filter_by_date(self):
        """Todo list --range filters by date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task A", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task B", "--at", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task A" in result.stdout
            assert "task B" not in result.stdout

    def test_todo_list_filter_by_time(self):
        """Todo list --time filters by time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "morning", "--at", "2026-06-16 09:00"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "afternoon", "--at", "2026-06-16 14:30"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--time", "14:30"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "afternoon" in result.stdout
            assert "morning" not in result.stdout

    def test_todo_list_filter_by_status(self):
        """Todo list --status filters by status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "pending task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID and complete it
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            run_cli(["todo", "complete", "--id", todo_id], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--status", "completed"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "pending task" in result.stdout

    def test_todo_list_json_output(self):
        """Todo list --json outputs JSONlines format (#60)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--json"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should be JSONlines format - each line is valid JSON
            lines = [line for line in result.stdout.split("\n") if line]
            assert len(lines) > 0
            data = json.loads(lines[0])
            assert isinstance(data, dict)
            assert data["text"] == "task"

    def test_todo_list_contains_filter(self):
        """Todo list --contains filters by substring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "write unit tests", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "write docs", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "review code", "--at", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--range", "2026-06-16", "--contains", "write"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "unit tests" in result.stdout
            assert "docs" in result.stdout
            assert "review" not in result.stdout


class TestTodoComplete:
    """Tests for todo complete command output format."""

    def test_todo_complete_output_format(self):
        """Todo complete outputs git-style format: [id] Completed: text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "Review PR", "--at", "2026-06-18"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            # Complete the todo
            result = run_cli(["todo", "complete", "--id", todo_id], cwd=Path(tmpdir))
            assert result.returncode == 0
            # Should output: [tXXXXX] Completed: Review PR
            assert f"[{todo_id}] Completed: Review PR" in result.stdout


class TestTodoAbandon:
    """Tests for todo abandon command output format."""

    def test_todo_abandon_output_format(self):
        """Todo abandon outputs git-style format: [id] Abandoned: text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "Old task", "--at", "2026-06-18"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            # Abandon the todo
            result = run_cli(["todo", "abandon", "--id", todo_id], cwd=Path(tmpdir))
            assert result.returncode == 0
            # Should output: [tXXXXX] Abandoned: Old task
            assert f"[{todo_id}] Abandoned: Old task" in result.stdout
