"""Tests for event commands (Issue #46 refactored)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


class TestEventAdd:
    """Tests for event add command (new API: TEXT --date DATE --time TIME)."""

    def test_event_add_creates_entry(self):
        """Tracer bullet: timeline-cli event add creates an event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            assert len(content) == 2

            record = json.loads(content[1])
            assert record["date"] == "2026-06-16"
            assert len(record["events"]) == 1
            assert record["events"][0]["time"] == "14:30"
            assert record["events"][0]["text"] == "meeting"

    def test_event_add_with_detail(self):
        """Event add with --detail parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                [
                    "event",
                    "add",
                    "meeting",
                    "--date",
                    "2026-06-16",
                    "--time",
                    "14:30",
                    "--detail",
                    "discussed project",
                ],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["events"][0]["details"] == ["discussed project"]

    def test_event_add_multiple_details(self):
        """Event add with multiple --detail parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                [
                    "event",
                    "add",
                    "meeting",
                    "--date",
                    "2026-06-16",
                    "--time",
                    "14:30",
                    "--detail",
                    "item 1",
                    "--detail",
                    "item 2",
                ],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["events"][0]["details"] == ["item 1", "item 2"]

    def test_event_add_to_existing_date(self):
        """Adding event to existing date appends and sorts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "morning", "--date", "2026-06-16", "--time", "10:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "afternoon", "--date", "2026-06-16", "--time", "14:30"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / "timelines.jsonl"
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert len(record["events"]) == 2
            # Should be sorted by time
            assert record["events"][0]["time"] == "10:00"
            assert record["events"][1]["time"] == "14:30"

    def test_event_add_requires_time(self):
        """Event add should fail without --time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            # argparse should enforce --time is required
            result = run_cli(["event", "add", "meeting", "--date", "2026-06-16"], cwd=Path(tmpdir))
            # argparse will show error before reaching our handler
            assert result.returncode != 0


class TestEventList:
    """Tests for event list command (new API: --range required)."""

    def test_event_list_shows_events(self):
        """Tracer bullet: timeline-cli event list shows events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "breakfast", "--date", "2026-06-16", "--time", "09:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "lunch", "--date", "2026-06-16", "--time", "12:00"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "09:00" in result.stdout
            assert "breakfast" in result.stdout
            assert "12:00" in result.stdout
            assert "lunch" in result.stdout

    def test_event_list_output_json(self):
        """Event list --output json outputs JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--range", "2026-06-16", "--output", "json"], cwd=Path(tmpdir))
            assert result.returncode == 0

            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["time"] == "14:30"

    def test_event_list_output_simple(self):
        """Event list --output simple outputs simple text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--range", "2026-06-16", "--output", "simple"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "14:30" in result.stdout
            assert "meeting" in result.stdout

    def test_event_list_contains_filter(self):
        """Event list --contains filters by substring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "team meeting", "--date", "2026-06-16", "--time", "10:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "lunch", "--date", "2026-06-16", "--time", "14:00"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--range", "2026-06-16", "--contains", "meeting"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "team meeting" in result.stdout
            assert "lunch" not in result.stdout
