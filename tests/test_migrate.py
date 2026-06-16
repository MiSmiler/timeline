"""Tests for migrate command and script (#12)."""

import json
import subprocess
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
                ["python", str(get_script_path()), str(tmpdir_path)],
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
                ["python", str(get_script_path()), str(tmpdir_path)],
                capture_output=True,
                text=True,
            )

            # Should succeed but skip invalid file
            assert result.returncode == 0
            assert "skip" in result.stdout.lower() or "invalid" in result.stdout.lower()