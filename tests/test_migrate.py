"""Tests for migrate command and script (#12)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from conftest import run_cli


def get_script_path() -> Path:
    """Get the path to migrate_from_markdown.py."""
    return Path(__file__).parent.parent / "scripts" / "migrate_from_markdown.py"


class TestMigrateCommand:
    """Tests for timeline-cli migrate command."""

    def test_migrate_to_same_version_fails(self):
        """Tracer bullet: migrate --to 1 on v1 file should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(["migrate", "--to", "1"], cwd=Path(tmpdir))
            assert result.returncode != 0
            assert "Already" in result.stderr or "already" in result.stderr.lower()


class TestMigrateFromMarkdown:
    """Tests for scripts/migrate_from_markdown.py."""

    def test_migrate_single_markdown_file(self):
        """Tracer bullet: migrate a single YYYY-MM-DD.md file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a markdown file
            md_file = tmpdir_path / "2026-06-16.md"
            md_file.write_text(
                """# 2026-06-16

## Events
- 09:00 Morning meeting. Discussed project timeline.
- 14:30 Code review session.

## Todos
- [ ] Write unit tests
- [x] Fix login bug
- [ ] ~~Review docs~~

## Notes
Good progress today.
"""
            )

            # Run migration script
            result = subprocess.run(
                [sys.executable, str(get_script_path()), str(tmpdir_path)],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # Check output file
            output_file = tmpdir_path / "timelines.jsonl"
            assert output_file.exists()

            content = output_file.read_text().strip().split("\n")
            header = json.loads(content[0])
            assert header["schema_version"] == 1

            record = json.loads(content[1])
            assert record["date"] == "2026-06-16"
            assert len(record["events"]) == 2
            assert len(record["todos"]) == 3
            assert record["notes"] == "Good progress today."

    def test_migrate_invalid_filename_skipped(self):
        """Files not matching YYYY-MM-DD.md should be skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create invalid filename
            md_file = tmpdir_path / "random-note.md"
            md_file.write_text("# Some note\n")

            result = subprocess.run(
                [sys.executable, str(get_script_path()), str(tmpdir_path)],
                capture_output=True,
                text=True,
            )

            # Should succeed but skip invalid file
            assert result.returncode == 0
            assert "skip" in result.stdout.lower() or "invalid" in result.stdout.lower()

    def test_todo_with_time(self):
        """Todo with HH:MM prefix should parse time correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            md_file = tmpdir_path / "2026-06-16.md"
            md_file.write_text(
                """# 2026-06-16

## Todos
- [x] 10:30 Fix login bug
"""
            )

            result = subprocess.run(
                [sys.executable, str(get_script_path()), str(tmpdir_path)],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            output_file = tmpdir_path / "timelines.jsonl"
            content = output_file.read_text().strip().split("\n")
            record = json.loads(content[1])

            assert len(record["todos"]) == 1
            todo = record["todos"][0]
            assert todo["time"] == "10:30"
            assert todo["text"] == "Fix login bug"
            assert todo["status"] == "completed"

    def test_todo_without_time(self):
        """Todo without HH:MM prefix should have time: null."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            md_file = tmpdir_path / "2026-06-16.md"
            md_file.write_text(
                """# 2026-06-16

## Todos
- [ ] Write unit tests
"""
            )

            result = subprocess.run(
                [sys.executable, str(get_script_path()), str(tmpdir_path)],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            output_file = tmpdir_path / "timelines.jsonl"
            content = output_file.read_text().strip().split("\n")
            record = json.loads(content[1])

            assert len(record["todos"]) == 1
            todo = record["todos"][0]
            assert todo["time"] is None
            assert todo["text"] == "Write unit tests"
            assert todo["status"] == "pending"

    def test_todo_with_indented_detail(self):
        """Todo with indented detail line should parse detail correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            md_file = tmpdir_path / "2026-06-16.md"
            md_file.write_text(
                """# 2026-06-16

## Todos
- [ ] Buy groceries
    - Need milk and eggs
"""
            )

            result = subprocess.run(
                [sys.executable, str(get_script_path()), str(tmpdir_path)],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            output_file = tmpdir_path / "timelines.jsonl"
            content = output_file.read_text().strip().split("\n")
            record = json.loads(content[1])

            assert len(record["todos"]) == 1
            todo = record["todos"][0]
            assert todo["time"] is None
            assert todo["text"] == "Buy groceries"
            assert todo["details"] == ["Need milk and eggs"]

    def test_todo_with_time_and_detail(self):
        """Todo with time and indented detail should parse both correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            md_file = tmpdir_path / "2026-06-16.md"
            md_file.write_text(
                """# 2026-06-16

## Todos
- [x] 14:30 Review docs
    - Check README and API docs
"""
            )

            result = subprocess.run(
                [sys.executable, str(get_script_path()), str(tmpdir_path)],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            output_file = tmpdir_path / "timelines.jsonl"
            content = output_file.read_text().strip().split("\n")
            record = json.loads(content[1])

            assert len(record["todos"]) == 1
            todo = record["todos"][0]
            assert todo["time"] == "14:30"
            assert todo["text"] == "Review docs"
            assert todo["status"] == "completed"
            assert todo["details"] == ["Check README and API docs"]

    def test_event_with_indented_detail(self):
        """Event with indented detail line should parse detail correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            md_file = tmpdir_path / "2026-06-16.md"
            md_file.write_text(
                """# 2026-06-16

## Events
- 10:00 Team meeting
    - Discussed Q3 roadmap
"""
            )

            result = subprocess.run(
                [sys.executable, str(get_script_path()), str(tmpdir_path)],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            output_file = tmpdir_path / "timelines.jsonl"
            content = output_file.read_text().strip().split("\n")
            record = json.loads(content[1])

            assert len(record["events"]) == 1
            event = record["events"][0]
            assert event["time"] == "10:00"
            assert event["text"] == "Team meeting"
            assert event["details"] == ["Discussed Q3 roadmap"]
