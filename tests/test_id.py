"""Tests for ID generation and lookup (Issue #42)."""

import json
import string
import tempfile
from pathlib import Path

from conftest import read_items_by_date, run_cli


class TestIDGeneration:
    """Tests for ID generation."""

    def test_todo_add_generates_id(self):
        """Todo add should generate a unique ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))

            # Add a todo (new API)
            result = run_cli(["todo", "add", "test task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Verify ID in output
            assert "[" in result.stdout
            assert "]" in result.stdout

            # Verify ID in storage
            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            todo = items["todos"][0]

            # ID should exist and have correct format
            assert "id" in todo
            assert todo["id"].startswith("t")
            assert len(todo["id"]) == 6  # 't' + 5 chars

    def test_event_add_generates_id(self):
        """Event add should generate a unique ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))

            # Add an event
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-16 14:30"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Verify ID in output
            assert "[" in result.stdout
            assert "]" in result.stdout

            # Verify ID in storage
            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            event = items["events"][0]

            # ID should exist and have correct format
            assert "id" in event
            assert event["id"].startswith("e")
            assert len(event["id"]) == 6  # 'e' + 5 chars

    def test_ids_are_unique(self):
        """Multiple todos should have different IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))

            # Add multiple todos (new API)
            run_cli(["todo", "add", "task 1", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 2", "--at", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task 3", "--at", "2026-06-17"], cwd=Path(tmpdir))

            # Verify IDs are unique
            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            from conftest import read_items_from_storage

            items = read_items_from_storage(storage_file)

            ids = []
            for todo in items["todos"]:
                ids.append(todo["id"])

            assert len(ids) == 3
            assert len(set(ids)) == 3  # All unique


class TestIDDisplay:
    """Tests for ID display in list commands."""

    def test_todo_list_shows_id(self):
        """Todo list --show-id should display ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))
            # Extract ID from output: "Added todo [t7b3k]: task"
            todo_id = result.stdout.split("[")[1].split("]")[0]

            # List todos with --show-id
            result = run_cli(["todo", "list", "--range", "2026-06-16", "--show-id"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Verify ID in output (format: (t7b3k))
            assert f"({todo_id})" in result.stdout

    def test_event_list_shows_id(self):
        """Event list --show-id should display ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["event", "add", "meeting", "--at", "2026-06-16 14:30"],
                cwd=Path(tmpdir),
            )
            # Extract ID from output: "Added event [e4x1m]: meeting at 14:30"
            event_id = result.stdout.split("[")[1].split("]")[0]

            # List events with --show-id
            result = run_cli(["event", "list", "--range", "2026-06-16", "--show-id"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Verify ID in output (format: (e4x1m))
            assert f"({event_id})" in result.stdout

    def test_json_output_includes_id(self):
        """JSON output should include id field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))

            # List todos with --json
            result = run_cli(["todo", "list", "--range", "2026-06-16", "--json"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Parse JSONlines output - first line is a JSON object
            lines = [line for line in result.stdout.split("\n") if line]
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert "id" in data
            assert data["id"].startswith("t")


class TestBackwardCompatibility:
    """Tests for backward compatibility with schema v1 data."""

    def test_reads_v1_data_without_id(self):
        """Should read v1 data (no id field) without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create v1 data manually (no id field)
            timeline_dir = Path(tmpdir) / ".timeline"
            timeline_dir.mkdir()
            storage_file = timeline_dir / "data.jsonl"
            content = [
                json.dumps({"schema_version": 1}),
                json.dumps(
                    {
                        "date": "2026-06-16",
                        "todos": [
                            {
                                "time": None,
                                "text": "legacy task",
                                "status": "pending",
                                "details": [],
                            }
                        ],
                        "events": [],
                        "notes": None,
                    }
                ),
            ]
            storage_file.write_text("\n".join(content) + "\n")

            # Should be able to list (new API: --range required)
            result = run_cli(["todo", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "legacy task" in result.stdout

    def test_list_without_id_still_works(self):
        """List command should work even when items have no ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create v1 data manually
            timeline_dir = Path(tmpdir) / ".timeline"
            timeline_dir.mkdir()
            storage_file = timeline_dir / "data.jsonl"
            content = [
                json.dumps({"schema_version": 1}),
                json.dumps(
                    {
                        "date": "2026-06-16",
                        "todos": [
                            {
                                "time": "10:00",
                                "text": "old task",
                                "status": "pending",
                                "details": [],
                            }
                        ],
                        "events": [],
                        "notes": None,
                    }
                ),
            ]
            storage_file.write_text("\n".join(content) + "\n")

            # List should work (new API)
            result = run_cli(["todo", "list", "--range", "2026-06-16"], cwd=Path(tmpdir))
            assert result.returncode == 0
            assert "old task" in result.stdout


class TestIDFormat:
    """Tests for ID format validation."""

    def test_todo_id_prefix(self):
        """Todo ID should start with 't'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["todos"][0]["id"].startswith("t")

    def test_event_id_prefix(self):
        """Event ID should start with 'e'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "meeting", "--at", "2026-06-16 14:30"],
                cwd=Path(tmpdir),
            )

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            assert items["events"][0]["id"].startswith("e")

    def test_id_charset(self):
        """ID should only use lowercase letters and digits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "task", "--at", "2026-06-16"], cwd=Path(tmpdir))

            storage_file = Path(tmpdir) / ".timeline/data.jsonl"
            items = read_items_by_date(storage_file, "2026-06-16")
            todo_id = items["todos"][0]["id"]

            # Check format: 't' followed by 5 lowercase/digits
            random_part = todo_id[1:]  # Skip prefix
            assert len(random_part) == 5
            assert all(c in string.ascii_lowercase + string.digits for c in random_part)
