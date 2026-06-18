"""Tests for note commands (#11)."""

import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestNoteAdd:
    """Tests for note add command."""

    def test_note_add_creates_note(self):
        """Tracer bullet: timeline-cli note add creates a note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["note", "add", "2026-06-16", "Today was productive"], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["notes"]) == 1
            assert items["notes"][0]["text"] == "Today was productive"

    def test_note_add_to_existing_date(self):
        """Adding note to date with existing todos/events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["note", "add", "2026-06-16", "good day"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["todos"]) == 1
            assert len(items["notes"]) == 1
            assert items["notes"][0]["text"] == "good day"

    def test_note_add_replaces_existing(self):
        """Note add replaces existing note (one note per date)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["note", "add", "2026-06-16", "first note"], cwd=Path(tmpdir))
            run_cli(["note", "add", "2026-06-16", "second note"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert len(items["notes"]) == 1
            assert items["notes"][0]["text"] == "second note"


class TestNoteShow:
    """Tests for note show command."""

    def test_note_show_displays_note(self):
        """Tracer bullet: timeline-cli note show displays note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["note", "add", "2026-06-16", "Today's thought"], cwd=Path(tmpdir))

            result = run_cli(["note", "show", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "Today's thought" in result.stdout

    def test_note_show_empty_note(self):
        """Note show for date with no note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["note", "show", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "No note" in result.stdout or result.stdout.strip() == ""

    def test_note_show_date_not_exist(self):
        """Note show for date that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["note", "show", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0


class TestNoteEdit:
    """Tests for note edit command."""

    def test_note_edit_updates_note(self):
        """Tracer bullet: timeline-cli note edit updates note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["note", "add", "2026-06-16", "old thought"], cwd=Path(tmpdir))

            result = run_cli(["note", "edit", "2026-06-16", "new thought"], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["notes"][0]["text"] == "new thought"

    def test_note_edit_creates_if_not_exist(self):
        """Note edit creates note if doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["note", "edit", "2026-06-16", "created note"], cwd=Path(tmpdir))
            assert result.returncode == 0

            storage_file = Path(tmpdir) / ".timelines.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["notes"][0]["text"] == "created note"
