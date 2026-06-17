"""Tests for event edit commands (Issue #46 refactored)."""

import json
import re
import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestEventEdit:
    """Tests for event edit command (new API: use --id)."""

    def test_event_edit_new_text(self):
        """Tracer bullet: timeline-cli event edit --new-text updates text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-text", "discussion"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["text"] == "discussion"

    def test_event_edit_new_time(self):
        """Event edit --new-time updates time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-time", "15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["time"] == "15:00"

    def test_event_edit_append_detail(self):
        """Event edit --append-detail adds detail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--append-detail", "notes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert "notes" in items["events"][0]["details"]

    def test_event_edit_set_detail(self):
        """Event edit --set-detail replaces all details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30", "--detail", "old"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                [
                    "event",
                    "edit",
                    "--id",
                    event_id,
                    "--set-detail",
                    "new 1",
                    "--set-detail",
                    "new 2",
                ],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["details"] == ["new 1", "new 2"]

    def test_event_edit_not_found(self):
        """Event edit fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["event", "edit", "--id", "e99999", "--new-text", "new"], cwd=Path(tmpdir))
            assert result.returncode != 0


class TestEventDelete:
    """Tests for event delete command (new API: use --id)."""

    def test_event_delete_with_confirmation(self):
        """Tracer bullet: timeline-cli event delete removes event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "delete", "--id", event_id, "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["events"]) == 0

    def test_event_delete_not_found(self):
        """Event delete fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["event", "delete", "--id", "e99999", "--yes"], cwd=Path(tmpdir))
            assert result.returncode != 0
