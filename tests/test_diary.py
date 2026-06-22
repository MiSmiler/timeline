"""Tests for diary command (#56)."""

import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from conftest import run_cli


class TestDiaryCommand:
    """Tests for diary command."""

    def test_diary_shows_today_event_todo_note(self):
        """TDD: timeline-cli diary shows today's Event + TODO + Note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = datetime.now().strftime("%Y-%m-%d")

            # Initialize
            run_cli(["init"], cwd=Path(tmpdir))

            # Add event for today
            run_cli(["event", "add", "Team meeting", "--date", today, "--time", "10:00"], cwd=Path(tmpdir))

            # Add todo for today
            run_cli(["todo", "add", "Finish report", "--date", today, "--time", "14:00"], cwd=Path(tmpdir))

            # Add note for today
            run_cli(["note", "add", today, "Good progress today"], cwd=Path(tmpdir))

            # Run diary command
            result = run_cli(["diary"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should show the date as header
            assert f"# {today}" in result.stdout

            # Should show Event section with event
            assert "## Event" in result.stdout
            assert "10:00 Team meeting" in result.stdout

            # Should show TODO section with todo
            assert "## TODO" in result.stdout
            assert "Finish report" in result.stdout

            # Should show Note section with note
            assert "## Note" in result.stdout
            assert "Good progress today" in result.stdout

    def test_diary_yesterday_shows_yesterdays_data(self):
        """TDD: timeline-cli diary yesterday shows yesterday's data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            today = date.today().isoformat()

            # Initialize
            run_cli(["init"], cwd=Path(tmpdir))

            # Add event for yesterday
            run_cli(["event", "add", "Yesterday meeting", "--date", yesterday, "--time", "09:00"], cwd=Path(tmpdir))

            # Add event for today (should not appear)
            run_cli(["event", "add", "Today meeting", "--date", today, "--time", "10:00"], cwd=Path(tmpdir))

            # Run diary yesterday
            result = run_cli(["diary", "yesterday"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should show yesterday's date
            assert f"# {yesterday}" in result.stdout

            # Should show yesterday's event
            assert "09:00 Yesterday meeting" in result.stdout

            # Should NOT show today's event
            assert "Today meeting" not in result.stdout

    def test_diary_show_id_displays_ids(self):
        """TDD: timeline-cli diary --show-id displays item IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today().isoformat()

            # Initialize
            run_cli(["init"], cwd=Path(tmpdir))

            # Add event
            result = run_cli(["event", "add", "Meeting", "--date", today, "--time", "10:00"], cwd=Path(tmpdir))
            event_id = result.stdout.split("[")[1].split("]")[0]

            # Add todo
            result = run_cli(["todo", "add", "Task", "--date", today, "--time", "14:00"], cwd=Path(tmpdir))
            todo_id = result.stdout.split("[")[1].split("]")[0]

            # Run diary --show-id
            result = run_cli(["diary", "--show-id"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should show event ID
            assert f"({event_id})" in result.stdout
            assert f"10:00 ({event_id}) Meeting" in result.stdout

            # Should show todo ID
            assert f"({todo_id})" in result.stdout

    def test_diary_empty_date_shows_empty_structure(self):
        """TDD: timeline-cli diary for date with no data shows empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize but don't add any data
            run_cli(["init"], cwd=Path(tmpdir))

            # Run diary for a specific date
            result = run_cli(["diary", "2026-06-18"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should show date header
            assert "# 2026-06-18" in result.stdout

            # Should show all sections even when empty
            assert "## Event" in result.stdout
            assert "## TODO" in result.stdout
            assert "## Note" in result.stdout

            # Should NOT have any items
            lines = result.stdout.split("\n")
            for line in lines:
                # Skip headers and empty lines
                if line.startswith("#") or line.startswith("##") or not line.strip():
                    continue
                # If it's not a header or empty, it shouldn't be an item
                assert not line.startswith("- ")

    def test_diary_with_details(self):
        """Test diary shows details indented under items."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today().isoformat()

            # Initialize
            run_cli(["init"], cwd=Path(tmpdir))

            # Add event with details
            run_cli(
                ["event", "add", "Meeting", "--date", today, "--time", "10:00", "--detail", "discussed timeline"],
                cwd=Path(tmpdir),
            )

            # Add todo with details
            run_cli(
                ["todo", "add", "Task", "--date", today, "--time", "14:00", "--detail", "need to review"],
                cwd=Path(tmpdir),
            )

            # Run diary
            result = run_cli(["diary"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should show details indented
            assert "    - discussed timeline" in result.stdout
            assert "    - need to review" in result.stdout

    def test_diary_todo_status_completed(self):
        """Test diary shows completed todos with [x] marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today().isoformat()

            # Initialize
            run_cli(["init"], cwd=Path(tmpdir))

            # Add and complete todo
            result = run_cli(["todo", "add", "Task", "--date", today], cwd=Path(tmpdir))
            todo_id = result.stdout.split("[")[1].split("]")[0]
            run_cli(["todo", "complete", "--id", todo_id], cwd=Path(tmpdir))

            # Run diary
            result = run_cli(["diary"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should show completed marker
            assert "- [x] Task" in result.stdout

    def test_diary_todo_status_abandoned(self):
        """Test diary shows abandoned todos with strikethrough."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today().isoformat()

            # Initialize
            run_cli(["init"], cwd=Path(tmpdir))

            # Add and abandon todo
            result = run_cli(["todo", "add", "Task", "--date", today], cwd=Path(tmpdir))
            todo_id = result.stdout.split("[")[1].split("]")[0]
            run_cli(["todo", "abandon", "--id", todo_id], cwd=Path(tmpdir))

            # Run diary
            result = run_cli(["diary"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should show abandoned marker with strikethrough
            assert "- [ ] ~~Task~~" in result.stdout

    def test_diary_specific_date(self):
        """Test diary with specific YYYY-MM-DD date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize
            run_cli(["init"], cwd=Path(tmpdir))

            # Add event for specific date
            run_cli(["event", "add", "Event", "--date", "2026-06-15", "--time", "10:00"], cwd=Path(tmpdir))

            # Run diary for that date
            result = run_cli(["diary", "2026-06-15"], cwd=Path(tmpdir))
            assert result.returncode == 0

            # Should show that date
            assert "# 2026-06-15" in result.stdout
            assert "10:00 Event" in result.stdout
