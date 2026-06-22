"""Tests for list command (#13, #57)."""

import tempfile
from pathlib import Path

from conftest import run_cli


class TestListCommand:
    """Tests for list command."""

    def test_list_default_markdown_output(self):
        """List command should output markdown format by default (#57)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            # Add events, todos, and notes to create test data
            run_cli(["todo", "add", "task1", "--at", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task2", "--at", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting", "--at", "2026-06-17 10:00"], cwd=Path(tmpdir))
            run_cli(["note", "add", "2026-06-17", "daily note"], cwd=Path(tmpdir))

            run_cli(["todo", "add", "task3", "--at", "2026-06-18"], cwd=Path(tmpdir))
            run_cli(["event", "add", "call", "--at", "2026-06-18 14:00"], cwd=Path(tmpdir))

            result = run_cli(["list"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Markdown format should show dates with counts
            assert "- 2026-06-17" in result.stdout
            assert "- 2026-06-18" in result.stdout
            # Should show counts: (1 event, 2 todos, 1 note)
            assert "1 event" in result.stdout or "1 events" in result.stdout
            assert "2 todo" in result.stdout or "2 todos" in result.stdout
            assert "1 note" in result.stdout or "1 notes" in result.stdout

    def test_list_json_flag_not_accepted(self):
        """List --json should not be accepted (#59)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(["list", "--json"], cwd=Path(tmpdir))
            # Should fail because --json is no longer supported
            assert result.returncode != 0
            # Should show error about unrecognized argument
            assert "unrecognized argument" in result.stderr or "error" in result.stderr.lower()

    def test_list_empty_file(self):
        """List on empty timeline shows 'No dates found'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["list"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "No dates found" in result.stdout

    def test_list_markdown_counts_correct(self):
        """List markdown should show correct counts for each date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            # Date 1: 3 events, 5 todos, 1 note
            run_cli(["todo", "add", "t1", "--at", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "t2", "--at", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "t3", "--at", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "t4", "--at", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "t5", "--at", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["event", "add", "e1", "--at", "2026-06-17 09:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "e2", "--at", "2026-06-17 10:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "e3", "--at", "2026-06-17 11:00"], cwd=Path(tmpdir))
            run_cli(["note", "add", "2026-06-17", "note1"], cwd=Path(tmpdir))

            # Date 2: 2 events, 3 todos, 1 note
            run_cli(["todo", "add", "t6", "--at", "2026-06-18"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "t7", "--at", "2026-06-18"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "t8", "--at", "2026-06-18"], cwd=Path(tmpdir))
            run_cli(["event", "add", "e4", "--at", "2026-06-18 14:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "e5", "--at", "2026-06-18 15:00"], cwd=Path(tmpdir))
            run_cli(["note", "add", "2026-06-18", "note2"], cwd=Path(tmpdir))

            result = run_cli(["list"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Check date order (sorted)
            lines = result.stdout.strip().split("\n")
            assert len(lines) == 2

            # First line should be 2026-06-17
            assert "2026-06-17" in lines[0]
            assert "3 event" in lines[0]
            assert "5 todo" in lines[0]
            assert "1 note" in lines[0]

            # Second line should be 2026-06-18
            assert "2026-06-18" in lines[1]
            assert "2 event" in lines[1]
            assert "3 todo" in lines[1]
            assert "1 note" in lines[1]
