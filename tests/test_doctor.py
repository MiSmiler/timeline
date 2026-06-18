"""Tests for doctor command (#18)."""

import json
import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestDoctor:
    """Tests for doctor command."""

    def test_doctor_valid_file_passes(self):
        """Tracer bullet: timeline-cli doctor passes for valid file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "All checks passed" in result.stdout

    def test_doctor_invalid_json_fails(self):
        """Doctor fails for invalid JSON line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            storage_file.write_text('{"schema_version": 1}\n{invalid json}')

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "invalid JSON" in result.stdout.lower() or "JSON" in result.stdout

    def test_doctor_missing_schema_version_fails(self):
        """Doctor fails for missing schema_version header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            storage_file.write_text('{"type": "todo", "date": "2026-06-16", "text": "task"}')

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "schema_version" in result.stdout.lower()

    def test_doctor_invalid_date_format_fails(self):
        """Doctor fails for invalid date format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n{"type": "todo", "date": "invalid-date", "text": "task", "status": "pending"}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "date" in result.stdout.lower()

    def test_doctor_invalid_status_fails(self):
        """Doctor fails for invalid todo status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n{"type": "todo", "date": "2026-06-16", "text": "task", "status": "invalid"}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "status" in result.stdout.lower()

    def test_doctor_fixes_sorting(self):
        """Doctor --fix auto-fixes sorting issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            # Create unsorted events (new format)
            storage_file.write_text(
                '{"schema_version": 1}\n'
                '{"type": "event", "date": "2026-06-16", "time": "15:00", "text": "B"}\n'
                '{"type": "event", "date": "2026-06-16", "time": "09:00", "text": "A"}'
            )

            result = run_cli(["doctor", "--fix"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Verify events are sorted
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["time"] == "09:00"
            assert items["events"][1]["time"] == "15:00"

    def test_doctor_undated_with_time_fails(self):
        """Doctor fails if undated todo has time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n'
                '{"type": "todo", "date": null, "text": "task", "status": "pending", "time": "14:30"}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0

    def test_doctor_event_without_date_fails(self):
        """Doctor fails if event has no date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n{"type": "event", "date": null, "time": "14:30", "text": "event"}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0

    def test_doctor_multiple_notes_same_date_fails(self):
        """Doctor fails if multiple notes for same date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n'
                '{"type": "note", "date": "2026-06-16", "text": "note 1"}\n'
                '{"type": "note", "date": "2026-06-16", "text": "note 2"}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "Multiple notes" in result.stdout

    def test_doctor_duplicate_id_fails(self):
        """Doctor fails if duplicate IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / ".timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n'
                '{"type": "todo", "id": "t123", "date": "2026-06-16", "text": "task 1", "status": "pending"}\n'
                '{"type": "todo", "id": "t123", "date": "2026-06-17", "text": "task 2", "status": "pending"}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "Duplicate ID" in result.stdout
