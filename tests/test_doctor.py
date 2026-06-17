"""Tests for doctor command (#18)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestDoctor:
    """Tests for doctor command."""

    def test_doctor_valid_file_passes(self):
        """Tracer bullet: timeline-cli doctor passes for valid file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "2026-06-16", "task"], cwd=Path(tmpdir))

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "All checks passed" in result.stdout

    def test_doctor_invalid_json_fails(self):
        """Doctor fails for invalid JSON line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            storage_file.write_text('{"schema_version": 1}\n{"date": "2026-06-16", "todos": [invalid json}')

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "invalid JSON" in result.stdout.lower() or "JSON" in result.stdout

    def test_doctor_missing_schema_version_fails(self):
        """Doctor fails for missing schema_version header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            storage_file.write_text('{"date": "2026-06-16", "todos": []}')

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "schema_version" in result.stdout.lower()

    def test_doctor_invalid_date_format_fails(self):
        """Doctor fails for invalid date format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            storage_file.write_text('{"schema_version": 1}\n{"date": "invalid-date", "todos": []}')

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "date" in result.stdout.lower()

    def test_doctor_duplicate_date_fails(self):
        """Doctor fails for duplicate dates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n{"date": "2026-06-16", "todos": []}\n{"date": "2026-06-16", "events": []}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "duplicate" in result.stdout.lower()

    def test_doctor_invalid_status_fails(self):
        """Doctor fails for invalid todo status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n{"date": "2026-06-16", "todos": [{"text": "task", "status": "invalid"}]}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "status" in result.stdout.lower()

    def test_doctor_fixes_sorting(self):
        """Doctor --fix auto-fixes sorting issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            # Create unsorted events
            storage_file.write_text(
                '{"schema_version": 1}\n'
                '{"date": "2026-06-16", "events": [{"time": "15:00", "text": "B"}, {"time": "09:00", "text": "A"}]}'
            )

            result = run_cli(["doctor", "--fix"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Verify events are sorted
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["events"][0]["time"] == "09:00"
            assert record["events"][1]["time"] == "15:00"

    def test_doctor_undated_with_time_fails(self):
        """Doctor fails if 0000-00-00 todo has time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n'
                '{"date": "0000-00-00", "todos": [{"text": "task", "status": "pending", "time": "14:30"}]}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0

    def test_doctor_undated_with_events_fails(self):
        """Doctor fails if 0000-00-00 has events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            storage_file.write_text(
                '{"schema_version": 1}\n{"date": "0000-00-00", "events": [{"time": "14:30", "text": "event"}]}'
            )

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0

    def test_doctor_undated_with_notes_fails(self):
        """Doctor fails if 0000-00-00 has notes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_file = Path(tmpdir) / "timelines.jsonl"
            storage_file.write_text('{"schema_version": 1}\n{"date": "0000-00-00", "notes": "some notes"}')

            result = run_cli(["doctor"], cwd=Path(tmpdir))
            assert result.returncode != 0
