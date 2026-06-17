"""Tests for event command refactoring (Issue #46)."""

import json
import re
import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestEventAddV2:
    """Tests for event add with new argument order: TEXT --date DATE --time TIME."""

    def test_event_add_new_order(self):
        """Event add should use new argument order: TEXT --date DATE --time TIME."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            # New argument order: TEXT --date DATE --time TIME
            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["events"]) == 1
            assert items["events"][0]["text"] == "meeting"
            assert items["events"][0]["time"] == "14:30"
            assert items["events"][0]["date"] == "2026-06-16"

    def test_event_add_with_detail(self):
        """Event add with --detail parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30", "--detail", "discussed project"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["details"] == ["discussed project"]

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

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["details"] == ["item 1", "item 2"]

    def test_event_add_requires_time(self):
        """Event add should fail without --time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            # argparse should enforce --time is required
            result = run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            # argparse will show error before reaching our handler
            assert result.returncode != 0


class TestEventListV2:
    """Tests for event list with --range as required parameter."""

    def test_event_list_requires_range(self):
        """Event list should require --range parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "meeting 1", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            run_cli(
                ["event", "add", "meeting 2", "--date", "2026-06-17", "--time", "10:00"],
                cwd=Path(tmpdir),
            )

            # Without --range should fail
            result = run_cli(["event", "list"], cwd=Path(tmpdir))
            assert result.returncode != 0

    def test_event_list_with_range(self):
        """Event list with --range parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "meeting 1", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            run_cli(
                ["event", "add", "meeting 2", "--date", "2026-06-17", "--time", "10:00"],
                cwd=Path(tmpdir),
            )

            result = run_cli(["event", "list", "--range", ".."], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "meeting 1" in result.stdout
            assert "meeting 2" in result.stdout

    def test_event_list_with_range_filter(self):
        """Event list --range should filter by date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "meeting A", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            run_cli(
                ["event", "add", "meeting B", "--date", "2026-06-17", "--time", "10:00"],
                cwd=Path(tmpdir),
            )

            result = run_cli(["event", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "meeting A" in result.stdout
            assert "meeting B" not in result.stdout

    def test_event_list_output_parameter(self):
        """Event list should support --output parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )

            result = run_cli(
                ["event", "list", "--range", "2026-06-16", "--output", "json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert len(data) == 1
            assert data[0]["text"] == "meeting"


class TestEventEditV2:
    """Tests for event edit with --id parameter."""

    def test_event_edit_new_text_by_id(self):
        """Event edit should use --id to locate event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "old meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            # Edit by ID
            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-text", "new meeting"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["text"] == "new meeting"

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
                ["event", "edit", "--id", event_id, "--new-time", "10:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["time"] == "10:00"

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
                ["event", "edit", "--id", event_id, "--append-detail", "extra info"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert "extra info" in items["events"][0]["details"]

    def test_event_edit_output_parameter(self):
        """Event edit should support --output parameter."""
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

            # Edit with --output json
            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-text", "new meeting", "--output", "json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output JSON
            data = json.loads(result.stdout)
            assert data["text"] == "new meeting"

    def test_event_edit_not_found(self):
        """Event edit fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["event", "edit", "--id", "e99999", "--new-text", "test"], cwd=Path(tmpdir))
            assert result.returncode != 0


class TestEventDeleteV2:
    """Tests for event delete with --id parameter."""

    def test_event_delete_by_id(self):
        """Event delete should use --id to locate event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting to delete", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            # Delete by ID with --yes to skip confirmation
            result = run_cli(["event", "delete", "--id", event_id, "--yes"], cwd=Path(tmpdir))
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
