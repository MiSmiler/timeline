"""Tests for --range parameter (Issue #43)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestRangeParameter:
    """Tests for --range parameter parsing and filtering."""

    def test_todo_list_with_range_today(self):
        """Todo list --range today should show today's todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            # Add todo for today and yesterday (new API)
            run_cli(["todo", "add", "today task", "--date", "2026-06-18"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "yesterday task", "--date", "2026-06-17"], cwd=Path(tmpdir))

            # List with --range today
            result = run_cli(["todo", "list", "--range", "today"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "today task" in result.stdout
            assert "yesterday task" not in result.stdout

    def test_todo_list_with_range_date(self):
        """Todo list --range YYYY-MM-DD should show that date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--date", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 17", "--date", "2026-06-17"], cwd=Path(tmpdir))

            # List with --range 2026-06-16
            result = run_cli(["todo", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 16" in result.stdout
            assert "task 15" not in result.stdout
            assert "task 17" not in result.stdout

    def test_todo_list_with_range_date_range(self):
        """Todo list --range start..end should show dates in range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 14", "--date", "2026-06-14"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--date", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 17", "--date", "2026-06-17"], cwd=Path(tmpdir))

            # List with --range 2026-06-15..2026-06-16
            result = run_cli(["todo", "list", "--range", "2026-06-15..2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 15" in result.stdout
            assert "task 16" in result.stdout
            assert "task 14" not in result.stdout
            assert "task 17" not in result.stdout

    def test_todo_list_with_range_open_end(self):
        """Todo list --range start.. should show dates from start onwards."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 14", "--date", "2026-06-14"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--date", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--date", "2026-06-16"], cwd=Path(tmpdir))

            # List with --range 2026-06-15..
            result = run_cli(["todo", "list", "--range", "2026-06-15.."], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 15" in result.stdout
            assert "task 16" in result.stdout
            assert "task 14" not in result.stdout

    def test_todo_list_with_range_open_start(self):
        """Todo list --range ..end should show dates up to end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--date", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 17", "--date", "2026-06-17"], cwd=Path(tmpdir))

            # List with --range ..2026-06-16
            result = run_cli(["todo", "list", "--range", "..2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 15" in result.stdout
            assert "task 16" in result.stdout
            assert "task 17" not in result.stdout

    def test_todo_list_with_range_all(self):
        """Todo list --range .. should show all todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 15", "--date", "2026-06-15"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 16", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 17", "--date", "2026-06-17"], cwd=Path(tmpdir))

            # List with --range ..
            result = run_cli(["todo", "list", "--range", ".."], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "task 15" in result.stdout
            assert "task 16" in result.stdout
            assert "task 17" in result.stdout

    def test_event_list_with_range(self):
        """Event list --range should filter events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "meeting 16", "--date", "2026-06-16", "--time", "10:00"],
                cwd=Path(tmpdir),
            )
            run_cli(
                ["event", "add", "meeting 17", "--date", "2026-06-17", "--time", "14:00"],
                cwd=Path(tmpdir),
            )

            # List with --range 2026-06-16
            result = run_cli(["event", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "meeting 16" in result.stdout
            assert "meeting 17" not in result.stdout

    def test_event_list_with_range_json(self):
        """Event list --range --output json should include date field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "10:00"],
                cwd=Path(tmpdir),
            )

            # List with --range and --output json
            result = run_cli(
                ["event", "list", "--range", "2026-06-16", "--output", "json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            data = json.loads(result.stdout)
            assert len(data) == 1
            assert data[0]["date"] == "2026-06-16"


class TestRangeBackwardCompatibility:
    """Tests for backward compatibility."""

    def test_event_list_with_positional_date_still_works(self):
        """Event list with positional date should still work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "10:00"],
                cwd=Path(tmpdir),
            )

            # List with positional date (legacy)
            result = run_cli(["event", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "meeting" in result.stdout
