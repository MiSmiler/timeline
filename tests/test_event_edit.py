"""Tests for event edit commands (#16)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestEventEdit:
    """Tests for event edit command."""

    def test_event_edit_new_text(self):
        """Tracer bullet: timeline-cli event edit --new-text updates text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "2026-06-16", "--time", "14:30", "meeting"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "edit", "2026-06-16", "14:30", "meeting", "--new-text", "discussion"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["events"][0]["text"] == "discussion"

    def test_event_edit_new_time(self):
        """Event edit --new-time updates time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "2026-06-16", "--time", "14:30", "meeting"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "edit", "2026-06-16", "14:30", "meeting", "--new-time", "15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["events"][0]["time"] == "15:00"

    def test_event_edit_append_detail(self):
        """Event edit --append-detail adds detail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "2026-06-16", "--time", "14:30", "meeting"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "edit", "2026-06-16", "14:30", "meeting", "--append-detail", "notes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert "notes" in record["events"][0]["details"]

    def test_event_edit_set_detail(self):
        """Event edit --set-detail replaces all details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "2026-06-16", "--time", "14:30", "--detail", "old", "meeting"], cwd=Path(tmpdir))

            result = run_cli(
                [
                    "event",
                    "edit",
                    "2026-06-16",
                    "14:30",
                    "meeting",
                    "--set-detail",
                    "new 1",
                    "--set-detail",
                    "new 2",
                ],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["events"][0]["details"] == ["new 1", "new 2"]

    def test_event_edit_not_found(self):
        """Event edit fails if event not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "edit", "2026-06-16", "14:30", "missing", "--new-text", "new"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0


class TestEventDelete:
    """Tests for event delete command."""

    def test_event_delete_with_confirmation(self):
        """Tracer bullet: timeline-cli event delete removes event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "2026-06-16", "--time", "14:30", "meeting"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "delete", "2026-06-16", "14:30", "meeting", "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert len(record["events"]) == 0

    def test_event_delete_not_found(self):
        """Event delete fails if event not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "delete", "2026-06-16", "14:30", "missing", "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0
