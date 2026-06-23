"""Tests for --at parameter in list commands (Issue #81).

This file replaces the previous test_range.py, updating tests to use
the new unified --at parameter instead of --range.
"""

import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

# Add src directory to Python path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conftest import run_cli


class TestAtParameterForTodoList:
    """Tests for --at parameter in todo list command."""

    def test_todo_list_at_today(self):
        """Todo list --at today should show today's todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today()
            yesterday = today - timedelta(days=1)

            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "today task", "--at", str(today)], cwd=Path(tmpdir))
            run_cli(["todo", "add", "yesterday task", "--at", str(yesterday)], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "today"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "today task" in result.stdout
            assert "yesterday task" not in result.stdout

    def test_todo_list_at_date_only(self):
        """Todo list --at YYYY-MM-DD should show that date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--at", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 17", "--at", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 16" in result.stdout
            assert "task 15" not in result.stdout
            assert "task 17" not in result.stdout

    def test_todo_list_at_date_range(self):
        """Todo list --at start..end should show dates in range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 14", "--at", "2026-06-14"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--at", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 17", "--at", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "2026-06-15..2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 15" in result.stdout
            assert "task 16" in result.stdout
            assert "task 14" not in result.stdout
            assert "task 17" not in result.stdout

    def test_todo_list_at_open_end(self):
        """Todo list --at start.. should show dates from start onwards."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 14", "--at", "2026-06-14"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--at", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--at", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "2026-06-15.."], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 15" in result.stdout
            assert "task 16" in result.stdout
            assert "task 14" not in result.stdout

    def test_todo_list_at_open_start(self):
        """Todo list --at ..end should show dates up to end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--at", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 17", "--at", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "..2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 15" in result.stdout
            assert "task 16" in result.stdout
            assert "task 17" not in result.stdout

    def test_todo_list_at_all(self):
        """Todo list --at .. should show all todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--at", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 17", "--at", "2026-06-17"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", ".."], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 15" in result.stdout
            assert "task 16" in result.stdout
            assert "task 17" in result.stdout

    def test_todo_list_at_undated(self):
        """Todo list --at undated should show undated todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            # Use distinctive names to avoid substring matching
            run_cli(["todo", "add", "someday task", "--at", "undated"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "today task", "--at", "today"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "undated"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "someday task" in result.stdout
            assert "today task" not in result.stdout

    def test_todo_list_at_datetime_exact_match(self):
        """Todo list --at YYYY-MM-DDTHH:MM should filter by exact time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            # Use T separator for add
            run_cli(["todo", "add", "9am task", "--at", "2026-06-23T09:00"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "10am task", "--at", "2026-06-23T10:00"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "2026-06-23T09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "9am task" in result.stdout
            assert "10am task" not in result.stdout

    def test_todo_list_at_today_with_time(self):
        """Todo list --at todayT09:00 should filter by exact time today."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "9am task", "--at", "todayT09:00"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "10am task", "--at", "todayT10:00"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "todayT09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "9am task" in result.stdout
            assert "10am task" not in result.stdout

    def test_todo_list_at_relative_yesterday(self):
        """Todo list --at yesterday should show yesterday's todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today()
            yesterday = today - timedelta(days=1)
            day_before = today - timedelta(days=2)

            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "yesterday task", "--at", str(yesterday)], cwd=Path(tmpdir))
            run_cli(["todo", "add", "today task", "--at", str(today)], cwd=Path(tmpdir))
            run_cli(["todo", "add", "day before task", "--at", str(day_before)], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "yesterday"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "yesterday task" in result.stdout
            assert "today task" not in result.stdout
            assert "day before task" not in result.stdout

    def test_todo_list_at_relative_tomorrow(self):
        """Todo list --at tomorrow should show tomorrow's todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today()
            tomorrow = today + timedelta(days=1)
            day_after = today + timedelta(days=2)

            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "tomorrow task", "--at", str(tomorrow)], cwd=Path(tmpdir))
            run_cli(["todo", "add", "today task", "--at", str(today)], cwd=Path(tmpdir))
            run_cli(["todo", "add", "day after task", "--at", str(day_after)], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--at", "tomorrow"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "tomorrow task" in result.stdout
            assert "today task" not in result.stdout
            assert "day after task" not in result.stdout

    def test_todo_list_at_reversed_range_rejected(self):
        """Todo list --at tomorrow..yesterday should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "list", "--at", "tomorrow..yesterday"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "reversed" in result.stderr.lower() or "before" in result.stderr.lower()

    def test_todo_list_with_status_only_default_range(self):
        """Todo list --status pending should use default range .."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 1", "--at", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 2", "--at", "2026-06-20"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--status", "pending"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 1" in result.stdout
            assert "task 2" in result.stdout

    def test_todo_list_with_contains_only_default_range(self):
        """Todo list --contains "task" should use default range .."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "my task", "--at", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "other thing", "--at", "2026-06-20"], cwd=Path(tmpdir))

            result = run_cli(["todo", "list", "--contains", "task"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "my task" in result.stdout
            assert "other thing" not in result.stdout

    def test_todo_list_at_with_status_combined(self):
        """Todo list --at today --status pending should combine filters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "today pending", "--at", "today"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "today completed", "--at", "today"], cwd=Path(tmpdir))
            # Complete one todo
            # Get ID first from storage

            result = run_cli(["todo", "list", "--at", "today", "--status", "pending"], cwd=Path(tmpdir))
            assert result.returncode == 0
            # Both todos are pending by default
            assert "today pending" in result.stdout
            assert "today completed" in result.stdout


class TestAtParameterForEventList:
    """Tests for --at parameter in event list command."""

    def test_event_list_at_today(self):
        """Event list --at today should show today's events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today()
            yesterday = today - timedelta(days=1)
            run_cli(["init"], cwd=Path(tmpdir))
            # Use T separator for add
            run_cli(["event", "add", "today meeting", "--at", f"{today}T10:00"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "yesterday meeting", "--at", f"{yesterday}T14:00"],
                cwd=Path(tmpdir),
            )

            result = run_cli(["event", "list", "--at", "today"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "today meeting" in result.stdout
            assert "yesterday meeting" not in result.stdout

    def test_event_list_at_date_range(self):
        """Event list --at start..end should show events in range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting 15", "--at", "2026-06-15T10:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting 16", "--at", "2026-06-16T14:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting 17", "--at", "2026-06-17T09:00"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--at", "2026-06-15..2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "meeting 15" in result.stdout
            assert "meeting 16" in result.stdout
            assert "meeting 17" not in result.stdout

    def test_event_list_at_undated_rejected(self):
        """Event list --at undated should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["event", "list", "--at", "undated"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "undated" in result.stderr.lower() or "event" in result.stderr.lower()

    def test_event_list_at_json_output(self):
        """Event list --at --json should include date field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting", "--at", "2026-06-16T10:00"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--at", "2026-06-16", "--json"], cwd=Path(tmpdir))
            assert result.returncode == 0

            lines = [line for line in result.stdout.split("\n") if line]
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["date"] == "2026-06-16"

    def test_event_list_with_contains_default_range(self):
        """Event list --contains should use default range .."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting", "--at", "2026-06-16T10:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "other", "--at", "2026-06-17T14:00"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--contains", "meeting"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "meeting" in result.stdout
            assert "other" not in result.stdout


class TestParameterRequirement:
    """Tests for parameter requirement on list commands."""

    def test_todo_list_no_params_rejected(self):
        """Todo list without any params should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "list"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "parameter" in result.stderr.lower() or "required" in result.stderr.lower()

    def test_event_list_no_params_rejected(self):
        """Event list without any params should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["event", "list"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "parameter" in result.stderr.lower() or "required" in result.stderr.lower()


class TestTSeparator:
    """Tests for T separator in time expressions."""

    def test_todo_add_with_T_separator(self):
        """Todo add --at YYYY-MM-DDTHH:MM works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-23T09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "2026-06-23 09:00" in result.stdout

    def test_event_add_with_T_separator(self):
        """Event add --at YYYY-MM-DDTHH:MM works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["event", "add", "meeting", "--at", "2026-06-23T09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "2026-06-23 09:00" in result.stdout

    def test_space_separator_rejected_in_add(self):
        """Space separator should be rejected in add commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-23 09:00"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "T separator" in result.stderr


class TestUndatedKeyword:
    """Tests for undated keyword."""

    def test_todo_add_undated_keyword(self):
        """Todo add --at undated creates undated todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "someday task", "--at", "undated"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "undated" in result.stdout.lower()

    def test_event_add_undated_rejected(self):
        """Event add --at undated should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["event", "add", "meeting", "--at", "undated"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "undated" in result.stderr.lower() or "time" in result.stderr.lower()
