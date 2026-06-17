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
            assert result.returncode == 0
            assert "Already" in result.stdout or "already" in result.stdout.lower()


class TestMigrateV2:
    """Tests for migrate --to 2 (Issue #47)."""

    def test_migrate_v2_assigns_ids(self):
        """Migrate to v2 assigns IDs to todos and events without IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a v1 timeline file with items without IDs
            storage_file = tmpdir_path / "timelines.jsonl"
            lines = [
                json.dumps({"schema_version": 1}),
                json.dumps({
                    "date": "2026-06-16",
                    "todos": [
                        {"time": "09:00", "text": "Task 1", "status": "pending", "details": []},
                        {"time": None, "text": "Task 2", "status": "pending", "details": []},
                    ],
                    "events": [{"time": "10:00", "text": "Meeting", "details": []}],
                    "notes": None,
                }),
                json.dumps({
                    "date": "2026-06-17",
                    "todos": [{"time": "14:00", "text": "Task 3", "status": "completed", "details": []}],
                    "events": [],
                    "notes": None,
                }),
            ]
            storage_file.write_text("\n".join(lines) + "\n")

            # Run migration
            result = run_cli(["migrate", "--to", "2"], cwd=tmpdir_path)

            assert result.returncode == 0
            assert "Migrated 4 items" in result.stdout

            # Verify file content
            content = storage_file.read_text().strip().split("\n")
            header = json.loads(content[0])
            assert header["schema_version"] == 2

            record1 = json.loads(content[1])
            assert len(record1["todos"]) == 2
            assert record1["todos"][0]["id"].startswith("t")
            assert len(record1["todos"][0]["id"]) == 6  # t + 5 chars
            assert record1["todos"][1]["id"].startswith("t")
            assert len(record1["events"]) == 1
            assert record1["events"][0]["id"].startswith("e")
            assert len(record1["events"][0]["id"]) == 6

            record2 = json.loads(content[2])
            assert len(record2["todos"]) == 1
            assert record2["todos"][0]["id"].startswith("t")

    def test_migrate_v2_preserves_existing_ids(self):
        """Migrate to v2 preserves existing IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a v1 timeline file with some items already having IDs
            storage_file = tmpdir_path / "timelines.jsonl"
            lines = [
                json.dumps({"schema_version": 1}),
                json.dumps({
                    "date": "2026-06-16",
                    "todos": [{"time": "09:00", "text": "Task 1", "status": "pending", "details": [], "id": "tcustom"}],
                    "events": [{"time": "10:00", "text": "Meeting", "details": []}],
                    "notes": None,
                }),
            ]
            storage_file.write_text("\n".join(lines) + "\n")

            # Run migration
            result = run_cli(["migrate", "--to", "2"], cwd=tmpdir_path)

            assert result.returncode == 0
            assert "Migrated 1 items" in result.stdout

            # Verify file content
            content = storage_file.read_text().strip().split("\n")
            record = json.loads(content[1])
            assert record["todos"][0]["id"] == "tcustom"  # Preserved
            assert record["events"][0]["id"].startswith("e")  # Assigned

    def test_migrate_v2_utf8_encoding(self):
        """Migrate to v2 writes UTF-8 encoded output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a v1 timeline file with Chinese characters
            storage_file = tmpdir_path / "timelines.jsonl"
            lines = [
                json.dumps({"schema_version": 1}),
                json.dumps({
                    "date": "2026-06-16",
                    "todos": [{"time": "09:00", "text": "测试任务", "status": "pending", "details": ["详情信息"]}],
                    "events": [{"time": "10:00", "text": "会议", "details": ["讨论项目"]}],
                    "notes": "今天天气不错",
                }),
            ]
            storage_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            # Run migration
            result = run_cli(["migrate", "--to", "2"], cwd=tmpdir_path)

            assert result.returncode == 0

            # Verify UTF-8 encoding (no escaped unicode)
            content = storage_file.read_text(encoding="utf-8")
            assert "测试任务" in content
            assert "详情信息" in content
            assert "会议" in content
            assert "讨论项目" in content
            assert "今天天气不错" in content
            # Ensure no unicode escapes like \u
            assert "\\u" not in content

    def test_migrate_v2_idempotent(self):
        """Migrate to v2 is idempotent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a v1 timeline file
            storage_file = tmpdir_path / "timelines.jsonl"
            lines = [
                json.dumps({"schema_version": 1}),
                json.dumps({
                    "date": "2026-06-16",
                    "todos": [{"time": "09:00", "text": "Task", "status": "pending", "details": []}],
                    "events": [],
                    "notes": None,
                }),
            ]
            storage_file.write_text("\n".join(lines) + "\n")

            # Run migration first time
            result1 = run_cli(["migrate", "--to", "2"], cwd=tmpdir_path)
            assert result1.returncode == 0

            # Read the assigned ID
            content1 = storage_file.read_text().strip().split("\n")
            record1 = json.loads(content1[1])
            todo_id1 = record1["todos"][0]["id"]

            # Run migration again
            result2 = run_cli(["migrate", "--to", "2"], cwd=tmpdir_path)
            assert result2.returncode == 0
            assert "Already at schema version 2" in result2.stdout

            # Verify ID didn't change
            content2 = storage_file.read_text().strip().split("\n")
            record2 = json.loads(content2[1])
            todo_id2 = record2["todos"][0]["id"]
            assert todo_id1 == todo_id2


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
