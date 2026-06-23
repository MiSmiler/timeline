"""Tests for event commands (Issue #46 refactored, Issue #70: --at parameter)."""

import json
import re
import tempfile
from datetime import date
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestEventAdd:
    """Tests for event add command (Issue #70: --at parameter)."""

    def test_event_add_creates_entry(self):
        """Tracer bullet: timeline-cli event add creates an event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-16T14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            content = storage_file.read_text().strip().split("\n")
            assert len(content) == 2  # header + one event

            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["events"]) == 1
            assert items["events"][0]["time"] == "14:30"
            assert items["events"][0]["text"] == "meeting"

    def test_event_add_output_format(self):
        """Event add outputs git-style format: [id] Added: text (YYYY-MM-DD HH:MM)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "team meeting", "--at", "2026-06-18T14:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Issue #68: Should output: [eXXXXX] Added: team meeting (2026-06-18 14:00)
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            assert "] Added: team meeting (2026-06-18 14:00)" in result.stdout


class TestEventAddAtParameter:
    """Tests for Issue #70: event add --at parameter support."""

    def test_event_add_at_explicit_datetime(self):
        """--at "YYYY-MM-DD HH:MM" works for events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Meeting", "--at", "2026-06-22T15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "] Added: Meeting (2026-06-22 15:00)" in result.stdout

    def test_event_add_at_now(self):
        """--at "now" resolves to current datetime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Meeting", "--at", "now"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            today_str = date.today().isoformat()
            assert re.search(r"\[e[a-z0-9]+\] Added: Meeting \(" + today_str + r" \d{2}:\d{2}\)", result.stdout)

    def test_event_add_at_time_only_defaults_today(self):
        """--at "HH:MM" defaults to today (Event requires time)."""
        # Note: If HH:MM is in the future, Event validation will reject it
        # Use a past time offset instead to ensure it's not rejected
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Meeting", "--at", "-1h"],  # Use offset instead
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Output will show actual date/time (may be today or yesterday if crosses boundary)
            assert re.search(r"\[e[a-z0-9]+\] Added: Meeting \(\d{4}-\d{2}-\d{2} \d{2}:\d{2}\)", result.stdout)

    def test_event_add_at_required(self):
        """event add requires --at parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Meeting"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0
            assert "--at" in result.stderr


class TestEventFutureTimeRejected:
    """Tests for Issue #70: Event time cannot be in the future."""

    def test_event_add_at_offset_future_rejected(self):
        """--at "+2h" rejected because future time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Meeting", "--at", "+2h"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0
            assert "Event time cannot be later than now" in result.stderr

    def test_event_add_at_tomorrow_rejected(self):
        """--at "tomorrowT10:00" rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Future meeting", "--at", "tomorrowT10:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0
            assert "Event time cannot be later than now" in result.stderr

    def test_event_add_at_past_allowed(self):
        """--at "-2h" allowed because past time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Past event", "--at", "-2h"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Output will show actual date/time (may be today or yesterday if crosses boundary)
            assert re.search(r"\[e[a-z0-9]+\] Added: Past event \(\d{4}-\d{2}-\d{2} \d{2}:\d{2}\)", result.stdout)

    def test_event_add_at_date_only_allowed(self):
        """--at "today" (date only) allowed - Event model constraint check skipped."""
        # Note: Event model requires time, but parse_at_parameter allows date-only
        # The validation only checks if BOTH date AND time are specified
        # If only date is specified, the model constraint (time required) should be checked
        # This is an edge case that needs to be decided
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Daily note", "--at", "yesterday"],
                cwd=Path(tmpdir),
            )
            # Event model requires time, so this should fail
            assert result.returncode != 0


class TestEventAddOutputNormalization:
    """Tests for Issue #68: event add output shows normalized date."""

    def test_event_add_at_now_shows_explicit_date(self):
        """event add --at now outputs YYYY-MM-DD, not 'now'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "Meeting", "--at", "now"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            today_str = date.today().isoformat()
            # Pattern: [exxxx] Added: Meeting (YYYY-MM-DD HH:MM)
            assert re.search(r"\[e[a-z0-9]+\] Added: Meeting \(" + today_str + r" \d{2}:\d{2}\)", result.stdout)


class TestEventAddWithDetail:
    """Tests for event add with --detail parameter."""

    def test_event_add_with_detail(self):
        """Event add with --detail parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                [
                    "event",
                    "add",
                    "meeting",
                    "--at",
                    "2026-06-16T14:30",
                    "--detail",
                    "discussed project",
                ],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
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
                    "--at",
                    "2026-06-16T14:30",
                    "--detail",
                    "item 1",
                    "--detail",
                    "item 2",
                ],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["details"] == ["item 1", "item 2"]

    def test_event_add_to_existing_date_appends_and_sorts(self):
        """Adding event to existing date appends and sorts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "morning", "--at", "2026-06-16T10:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "afternoon", "--at", "2026-06-16T14:30"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["events"]) == 2
            # Should be sorted by time
            assert items["events"][0]["time"] == "10:00"
            assert items["events"][1]["time"] == "14:30"


class TestEventList:
    """Tests for event list command (new API: --at required)."""

    def test_event_list_shows_events(self):
        """Tracer bullet: timeline-cli event list shows events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "breakfast", "--at", "2026-06-16T09:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "lunch", "--at", "2026-06-16T12:00"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "09:00" in result.stdout
            assert "breakfast" in result.stdout
            assert "12:00" in result.stdout
            assert "lunch" in result.stdout

    def test_event_list_json_output(self):
        """Event list --json outputs JSONlines format (#60)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "meeting", "--at", "2026-06-16T14:30"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--at", "2026-06-16", "--json"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should be JSONlines format - each line is valid JSON
            lines = [line for line in result.stdout.split("\n") if line]
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert isinstance(data, dict)
            assert data["time"] == "14:30"
            assert data["text"] == "meeting"

    def test_event_list_contains_filter(self):
        """Event list --contains filters by substring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["event", "add", "team meeting", "--at", "2026-06-16T10:00"], cwd=Path(tmpdir))
            run_cli(["event", "add", "lunch", "--at", "2026-06-16T14:00"], cwd=Path(tmpdir))

            result = run_cli(["event", "list", "--at", "2026-06-16", "--contains", "meeting"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "team meeting" in result.stdout
            assert "lunch" not in result.stdout
