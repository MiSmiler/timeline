"""Tests for event edit commands (Issue #70: --new-at parameter)."""

import re
import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestEventEdit:
    """Tests for event edit command (Issue #70: use --id, --new-at)."""

    def test_event_edit_new_text(self):
        """Event edit --new-text updates text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 14:30"],
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
            items = read_items_by_date(storage_file, "2026-06-15")
            assert items["events"][0]["text"] == "discussion"

    def test_event_edit_new_text_output_format(self):
        """Event edit --new-text outputs: [id] Edited: old → new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "old meeting", "--at", "2026-06-15 14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-text", "new meeting"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [eXXXXX] Edited: old meeting → new meeting
            assert f"[{event_id}] Edited: old meeting → new meeting" in result.stdout

    def test_event_edit_new_at_time_only(self):
        """Event edit --new-at updates time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-at", "2026-06-15 15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-15")
            assert items["events"][0]["time"] == "15:00"

    def test_event_edit_new_at_time_output_format(self):
        """Event edit --new-at outputs: [id] Edited: time: old → new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-at", "2026-06-15 15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [eXXXXX] Edited: time: 14:30 → 15:00
            assert f"[{event_id}] Edited: time: 14:30 → 15:00" in result.stdout

    def test_event_edit_new_at_date_change(self):
        """Event edit --new-at moves event to different date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 10:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-at", "2026-06-16 10:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            # Should no longer be in 2026-06-15
            items_old = read_items_by_date(storage_file, "2026-06-15")
            assert len(items_old["events"]) == 0
            # Should be in 2026-06-16
            items_new = read_items_by_date(storage_file, "2026-06-16")
            assert len(items_new["events"]) == 1

    def test_event_edit_new_at_date_only_rejected(self):
        """Event edit --new-at date-only (no time) is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 10:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-at", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0
            assert "Event must have a time" in result.stderr

    def test_event_edit_new_at_future_rejected(self):
        """Event edit --new-at future time is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "-1h"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-at", "+2h"],
                cwd=Path(tmpdir),
            )
            assert result.returncode != 0
            assert "Event time cannot be later than now" in result.stderr

    def test_event_edit_new_at_past_allowed(self):
        """Event edit --new-at past time is allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "-1h"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-at", "-30m"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output with actual date/time
            assert re.search(r"\[e[a-z0-9]+\] Edited:", result.stdout)

    def test_event_edit_append_detail(self):
        """Event edit --append-detail adds detail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 14:30"],
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
            items = read_items_by_date(storage_file, "2026-06-15")
            assert "notes" in items["events"][0]["details"]

    def test_event_edit_append_detail_output_format(self):
        """Event edit --append-detail outputs: [id] Edited: + detail: text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 14:30"],
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
            # Should output: [eXXXXX] Edited: + detail: notes
            assert f"[{event_id}] Edited: + detail: notes" in result.stdout

    def test_event_edit_set_detail(self):
        """Event edit --set-detail replaces all details (newline-separated)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 14:30", "--detail", "old"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            # Issue #54: Use \n separator instead of multiple --set-detail flags
            result = run_cli(
                ["event", "edit", "--id", event_id, "--set-detail", "new 1\nnew 2"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-15")
            assert items["events"][0]["details"] == ["new 1", "new 2"]

    def test_event_edit_set_detail_output_format(self):
        """Event edit --set-detail outputs: [id] Edited: details: old → new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 14:30", "--detail", "old"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            # Issue #54: Use \n separator
            result = run_cli(
                ["event", "edit", "--id", event_id, "--set-detail", "new 1\nnew 2"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [eXXXXX] Edited: details: old → new 1, new 2
            assert f"[{event_id}] Edited: details: old → new 1, new 2" in result.stdout

    def test_event_edit_multiple_changes_output_format(self):
        """Event edit with multiple flags shows multi-line diff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "old meeting", "--at", "2026-06-15 14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-text", "new meeting", "--new-at", "2026-06-15 15:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output multi-line diff:
            # [eXXXXX] Edited:
            #   text: old meeting → new meeting
            #   time: 14:30 → 15:00
            assert f"[{event_id}] Edited:" in result.stdout
            assert "text: old meeting → new meeting" in result.stdout
            assert "time: 14:30 → 15:00" in result.stdout

    def test_event_edit_not_found(self):
        """Event edit fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["event", "edit", "--id", "e99999", "--new-text", "new"], cwd=Path(tmpdir))
            assert result.returncode != 0


class TestEventDelete:
    """Tests for event delete command (new API: use --id)."""

    def test_event_delete_with_confirmation(self):
        """Event delete removes event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-15 14:30"],
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
            items = read_items_by_date(storage_file, "2026-06-15")
            assert len(items["events"]) == 0

    def test_event_delete_output_format(self):
        """Event delete outputs git-style format: [id] Deleted: text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "old meeting", "--at", "2026-06-15 14:30"],
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
            # Should output: [eXXXXX] Deleted: old meeting
            assert f"[{event_id}] Deleted: old meeting" in result.stdout

    def test_event_delete_not_found(self):
        """Event delete fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["event", "delete", "--id", "e99999", "--yes"], cwd=Path(tmpdir))
            assert result.returncode != 0
