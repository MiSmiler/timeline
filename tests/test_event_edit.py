"""Tests for event edit commands (Issue #46 refactored)."""

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

    def test_event_edit_new_text_output_format(self):
        """Event edit --new-text outputs: [id] Edited: old → new."""
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

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-text", "new meeting"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [eXXXXX] Edited: old meeting → new meeting
            assert f"[{event_id}] Edited: old meeting → new meeting" in result.stdout

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

    def test_event_edit_new_time_output_format(self):
        """Event edit --new-time outputs: [id] Edited: time: old → new."""
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
            # Should output: [eXXXXX] Edited: time: 14:30 → 15:00
            assert f"[{event_id}] Edited: time: 14:30 → 15:00" in result.stdout

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

    def test_event_edit_append_detail_output_format(self):
        """Event edit --append-detail outputs: [id] Edited: + detail: text."""
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
            # Should output: [eXXXXX] Edited: + detail: notes
            assert f"[{event_id}] Edited: + detail: notes" in result.stdout

    def test_event_edit_set_detail(self):
        """Event edit --set-detail replaces all details (newline-separated)."""
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

            # Issue #54: Use \n separator instead of multiple --set-detail flags
            result = run_cli(
                ["event", "edit", "--id", event_id, "--set-detail", "new 1\nnew 2"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["details"] == ["new 1", "new 2"]

    def test_event_edit_set_detail_output_format(self):
        """Event edit --set-detail outputs: [id] Edited: details: old → new."""
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
                ["event", "add", "old meeting", "--date", "2026-06-16", "--time", "14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(e[a-z0-9]+)\]", result.stdout)
            assert match is not None
            event_id = match.group(1)

            result = run_cli(
                ["event", "edit", "--id", event_id, "--new-text", "new meeting", "--new-time", "15:00"],
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

    def test_event_delete_output_format(self):
        """Event delete outputs git-style format: [id] Deleted: text."""
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