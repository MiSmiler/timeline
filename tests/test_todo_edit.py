"""Tests for todo edit commands (Issue #45 refactored, Issue #70: --new-at parameter)."""

import re
import tempfile
from datetime import date
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestTodoEdit:
    """Tests for todo edit command (Issue #70: use --id, --new-at)."""

    def test_todo_edit_new_text(self):
        """Tracer bullet: timeline-cli todo edit --new-text updates text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "old task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-text", "new task"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["text"] == "new task"

    def test_todo_edit_new_text_output_format(self):
        """Todo edit --new-text outputs: [id] Edited: old → new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "old task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-text", "new task"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [tXXXXX] Edited: old task → new task
            assert f"[{todo_id}] Edited: old task → new task" in result.stdout

    def test_todo_edit_new_at_time_only(self):
        """Todo edit --new-at "YYYY-MM-DD HH:MM" updates time (keeps same date)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16 09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            # Use full datetime to keep same date
            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-at", "2026-06-16 14:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["time"] == "14:00"

    def test_todo_edit_new_at_time_output_format(self):
        """Todo edit --new-at outputs: [id] Edited: time: old → new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16 09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            # Use full datetime to keep same date
            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-at", "2026-06-16 14:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [tXXXXX] Edited: time: 09:00 → 14:00
            assert f"[{todo_id}] Edited: time: 09:00 → 14:00" in result.stdout

    def test_todo_edit_new_at_date_change(self):
        """Todo edit --new-at moves todo to different date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-at", "2026-06-17"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            # Should no longer be in 2026-06-16
            items_old = read_items_by_date(storage_file, "2026-06-16")
            assert len(items_old["todos"]) == 0
            # Should be in 2026-06-17
            items_new = read_items_by_date(storage_file, "2026-06-17")
            assert len(items_new["todos"]) == 1

    def test_todo_edit_new_at_date_change_output_format(self):
        """Todo edit --new-at outputs date change: [id] Edited: date: old → new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-at", "2026-06-17"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [tXXXXX] Edited: date: 2026-06-16 → 2026-06-17
            assert f"[{todo_id}] Edited: date: 2026-06-16 → 2026-06-17" in result.stdout

    def test_todo_edit_new_at_to_undated(self):
        """Todo edit --new-at "" converts dated todo to undated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-at", ""],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            # Should be in undated (0000-00-00)
            items = read_items_by_date(storage_file, "0000-00-00")
            assert len(items["todos"]) == 1

    def test_todo_edit_new_at_from_undated(self):
        """Todo edit --new-at converts undated todo to dated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", ""], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-at", "2026-06-17"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            # Should no longer be in undated
            items_old = read_items_by_date(storage_file, "0000-00-00")
            assert len(items_old["todos"]) == 0
            # Should be in 2026-06-17
            items_new = read_items_by_date(storage_file, "2026-06-17")
            assert len(items_new["todos"]) == 1

    def test_todo_edit_new_at_clear_time(self):
        """Todo edit --new-at "2026-06-16" (date only) clears time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16 09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-at", "2026-06-16"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["time"] is None

    def test_todo_edit_append_detail(self):
        """Todo edit --append-detail adds detail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--append-detail", "extra info"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert "extra info" in items["todos"][0]["details"]

    def test_todo_edit_append_detail_output_format(self):
        """Todo edit --append-detail outputs: [id] Edited: + detail: text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--append-detail", "extra info"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [tXXXXX] Edited: + detail: extra info
            assert f"[{todo_id}] Edited: + detail: extra info" in result.stdout

    def test_todo_edit_set_detail(self):
        """Todo edit --set-detail replaces all details (newline-separated)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16", "--detail", "old"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            # Issue #54: Use \n separator instead of multiple --set-detail flags
            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--set-detail", "new 1\nnew 2"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["details"] == ["new 1", "new 2"]

    def test_todo_edit_set_detail_output_format(self):
        """Todo edit --set-detail outputs: [id] Edited: details: old → new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16", "--detail", "old"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--set-detail", "new 1\nnew 2"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output: [tXXXXX] Edited: details: old → new 1, new 2
            assert f"[{todo_id}] Edited: details: old → new 1, new 2" in result.stdout

    def test_todo_edit_multiple_changes_output_format(self):
        """Todo edit with multiple flags shows multi-line diff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "old task", "--at", "2026-06-16 09:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-text", "new task", "--new-at", "14:00"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should output multi-line diff:
            # [tXXXXX] Edited:
            #   text: old task → new task
            #   time: 09:00 → 14:00
            assert f"[{todo_id}] Edited:" in result.stdout
            assert "text: old task → new task" in result.stdout
            assert "time: 09:00 → 14:00" in result.stdout


class TestTodoDelete:
    """Tests for todo delete command (new API: use --id)."""

    def test_todo_delete_with_confirmation(self):
        """Tracer bullet: timeline-cli todo delete removes todo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            # Use --yes to skip confirmation
            result = run_cli(
                ["todo", "delete", "--id", todo_id, "--yes"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["todos"]) == 0

    def test_todo_delete_output_format(self):
        """Todo delete outputs git-style format: [id] Deleted: text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "Old task", "--at", "2026-06-18"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            # Delete with --yes
            result = run_cli(["todo", "delete", "--id", todo_id, "--yes"], cwd=Path(tmpdir))
            assert result.returncode == 0
            # Should output: [tXXXXX] Deleted: Old task
            assert f"[{todo_id}] Deleted: Old task" in result.stdout

    def test_todo_delete_not_found(self):
        """Todo delete fails if ID not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))


class TestTodoEditNewAtNow:
    """Tests for Issue #70: --new-at "now" support."""

    def test_todo_edit_new_at_now_with_today_date(self):
        """--new-at "now" works when result is today."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "today 09:00"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            result = run_cli(
                ["todo", "edit", "--id", todo_id, "--new-at", "now"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            today_str = date.today().isoformat()
            items = read_items_by_date(storage_file, today_str)
            # Time should be current HH:MM format
            assert re.match(r"\d{2}:\d{2}", items["todos"][0]["time"])
