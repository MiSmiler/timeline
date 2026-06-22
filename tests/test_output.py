"""Tests for output format simplification (Issue #51)."""

import json
import sys
import tempfile
from datetime import date
from pathlib import Path

# Add src directory to PYTHONPATH for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conftest import run_cli


class TestMarkdownOutput:
    """Tests for markdown output format (Issue #51)."""

    def test_todo_list_default_markdown(self):
        """Todo list should default to markdown output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Buy groceries", "--date", "2026-06-18"], cwd=Path(tmpdir))

            # List without --output flag (should be markdown by default)
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Markdown should have date as header
            assert "# 2026-06-18" in result.stdout
            assert "Buy groceries" in result.stdout

    def test_todo_list_markdown_with_time(self):
        """Todo list markdown should show time if present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["todo", "add", "Meeting", "--date", "2026-06-18", "--time", "14:30"],
                cwd=Path(tmpdir),
            )

            # List
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "# 2026-06-18" in result.stdout
            assert "14:30" in result.stdout
            assert "Meeting" in result.stdout

    def test_todo_list_json_flag(self):
        """Todo list --json should output JSONlines format (#60)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 1", "--date", "2026-06-18"], cwd=Path(tmpdir))

            # List with --json flag
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Verify JSONlines format - each line is valid JSON
            lines = [line for line in result.stdout.split("\n") if line]
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["text"] == "Task 1"
            # Verify field order: id should be first
            keys = list(data.keys())
            assert keys[0] == "id"

    def test_todo_list_markdown_grouped_by_date(self):
        """Todo list markdown should group todos by date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 1", "--date", "2026-06-17"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 2", "--date", "2026-06-18"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 3", "--date", "2026-06-18"], cwd=Path(tmpdir))

            # List
            result = run_cli(
                ["todo", "list", "--range", ".."],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should have two date headers
            assert "# 2026-06-17" in result.stdout
            assert "# 2026-06-18" in result.stdout
            assert "Task 1" in result.stdout
            assert "Task 2" in result.stdout
            assert "Task 3" in result.stdout

    def test_todo_list_markdown_with_details(self):
        """Todo list markdown should show details indented under item."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["todo", "add", "Buy groceries", "--date", "2026-06-18", "--detail", "Milk", "--detail", "Bread"],
                cwd=Path(tmpdir),
            )

            # List
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "# 2026-06-18" in result.stdout
            assert "Buy groceries" in result.stdout
            # Details should be indented
            assert "  - Milk" in result.stdout
            assert "  - Bread" in result.stdout

    def test_todo_list_markdown_with_show_id(self):
        """Todo list --show-id should show ID in markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task 1", "--date", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            # Extract ID from output: "Added todo [t7b3k]: Task 1"
            todo_id = result.stdout.split("[")[1].split("]")[0]

            # List with --show-id
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18", "--show-id"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "# 2026-06-18" in result.stdout
            # Should show ID in format (t7b3k)
            assert f"({todo_id})" in result.stdout
            assert "Task 1" in result.stdout

    def test_todo_list_markdown_undated(self):
        """Todo list markdown should show undated todos under # Undated header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup - create undated todo (no time)
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Sometime task", "--date", "0000-00-00"], cwd=Path(tmpdir))

            # List with --range ? (undated items)
            result = run_cli(
                ["todo", "list", "--range", "?"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "# Undated" in result.stdout
            assert "Sometime task" in result.stdout

    def test_todo_list_json_multiple_items(self):
        """Todo list --json should output one JSON object per line (#60)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 1", "--date", "2026-06-18"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task 2", "--date", "2026-06-18"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "list", "--range", "2026-06-18", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            lines = [line for line in result.stdout.split("\n") if line]
            assert len(lines) == 2
            data1 = json.loads(lines[0])
            data2 = json.loads(lines[1])
            assert data1["text"] == "Task 1"
            assert data2["text"] == "Task 2"

    def test_todo_list_json_empty_results(self):
        """Todo list --json with no results should output empty stdout, stderr message (#60)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "list", "--range", "2026-06-18", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == ""
            assert "No todos found" in result.stderr

    def test_json_output_chinese_characters(self):
        """JSON output should handle Chinese characters correctly (#60)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "买牛奶", "--date", "2026-06-18"], cwd=Path(tmpdir))

            result = run_cli(
                ["todo", "list", "--range", "2026-06-18", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should not be escaped as \uXXXX
            assert "买牛奶" in result.stdout
            assert "\\u" not in result.stdout

    def test_event_list_json_jsonlines_format(self):
        """Event list --json should output JSONlines format (#60)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "Meeting", "--date", "2026-06-18", "--time", "10:00"],
                cwd=Path(tmpdir),
            )

            result = run_cli(
                ["event", "list", "--range", "2026-06-18", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0

            # Verify JSONlines format
            lines = [line for line in result.stdout.split("\n") if line]
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["text"] == "Meeting"
            # Verify field order: id should be first
            keys = list(data.keys())
            assert keys[0] == "id"

    def test_event_list_json_empty_results(self):
        """Event list --json with no results should output empty stdout, stderr message (#60)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_cli(["init"], cwd=Path(tmpdir))

            result = run_cli(
                ["event", "list", "--range", "2026-06-18", "--json"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert result.stdout.strip() == ""
            assert "No events found" in result.stderr


class TestContainsParameter:
    """Tests for --contains parameter."""

    def test_todo_list_contains_match(self):
        """Todo list --contains should filter by substring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "buy groceries", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "buy milk", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "call mom", "--date", "2026-06-16"], cwd=Path(tmpdir))

            # List with --contains buy (new API)
            result = run_cli(
                ["todo", "list", "--range", "2026-06-16", "--contains", "buy"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "groceries" in result.stdout
            assert "milk" in result.stdout
            assert "mom" not in result.stdout

    def test_todo_list_contains_with_range(self):
        """Todo list --contains should work with --range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "meeting with team", "--date", "2026-06-16"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "call team lead", "--date", "2026-06-17"], cwd=Path(tmpdir))

            # List with --range and --contains (new API)
            result = run_cli(
                ["todo", "list", "--range", "..", "--contains", "team"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "meeting with team" in result.stdout
            assert "call team lead" in result.stdout

    def test_event_list_contains_match(self):
        """Event list --contains should filter by substring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(
                ["event", "add", "team meeting", "--date", "2026-06-16", "--time", "10:00"],
                cwd=Path(tmpdir),
            )
            run_cli(
                ["event", "add", "lunch", "--date", "2026-06-16", "--time", "14:00"],
                cwd=Path(tmpdir),
            )

            # List with --contains meeting
            result = run_cli(
                ["event", "list", "--range", "2026-06-16", "--contains", "meeting"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "team meeting" in result.stdout
            assert "lunch" not in result.stdout

    def test_todo_list_completed_status_as_checkbox(self):
        """Todo list should show completed status as [x]."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--date", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            todo_id = result.stdout.split("[")[1].split("]")[0]
            run_cli(["todo", "complete", "--id", todo_id], cwd=Path(tmpdir))

            # List
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "- [x] Task" in result.stdout

    def test_todo_list_abandoned_status_with_strikethrough(self):
        """Todo list should show abandoned status with strikethrough."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            result = run_cli(
                ["todo", "add", "Task", "--date", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            todo_id = result.stdout.split("[")[1].split("]")[0]
            run_cli(["todo", "abandon", "--id", todo_id], cwd=Path(tmpdir))

            # List
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            assert "- [ ] ~~Task~~" in result.stdout

    def test_todo_list_no_time_no_placeholder(self):
        """Todo list should not show - placeholder for untimed todos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            run_cli(["init"], cwd=Path(tmpdir))
            run_cli(["todo", "add", "Task", "--date", "2026-06-18"], cwd=Path(tmpdir))

            # List
            result = run_cli(
                ["todo", "list", "--range", "2026-06-18"],
                cwd=Path(tmpdir),
            )
            assert result.returncode == 0
            # Should NOT have "- - [ ] Task" (no placeholder dash)
            assert "- [ ] Task" in result.stdout
            assert "- - [ ] Task" not in result.stdout

    def test_format_event_item_component(self):
        """_format_event_item should format single event correctly."""
        from timeline_cli.models import Event
        from timeline_cli.output_formatter import _format_event_item

        # Event without ID
        event = Event(time="10:00", text="Meeting", details=["discussed timeline"])
        result = _format_event_item(event, show_id=False)
        assert result == "- 10:00 Meeting\n  - discussed timeline"

        # Event with ID
        event_with_id = Event(time="14:00", text="Workshop", details=[], id="e123")
        result = _format_event_item(event_with_id, show_id=True)
        assert result == "- 14:00 (e123) Workshop"

    def test_format_todo_item_component(self):
        """_format_todo_item should format single todo correctly."""
        from timeline_cli.models import Todo
        from timeline_cli.output_formatter import _format_todo_item

        # Pending todo without time
        todo = Todo(time=None, text="Task", status="pending", details=["detail1"])
        result = _format_todo_item(todo, show_id=False)
        assert result == "- [ ] Task\n  - detail1"

        # Completed todo with time
        todo_completed = Todo(time="14:00", text="Done", status="completed", details=[])
        result = _format_todo_item(todo_completed, show_id=False)
        assert result == "- [x] 14:00 Done"

        # Abandoned todo with ID
        todo_abandoned = Todo(time=None, text="Old", status="abandoned", details=[], id="t123")
        result = _format_todo_item(todo_abandoned, show_id=True)
        assert result == "- [ ] (t123) ~~Old~~"
