"""Tests for export commands (#17)."""

import re
import tempfile
from pathlib import Path

from conftest import run_cli


class TestExport:
    """Tests for export command."""

    def test_export_creates_markdown_file(self):
        """Tracer bullet: timeline-cli export creates markdown file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)
            result = run_cli(["todo", "add", "write tests", "--date", "2026-06-16"], cwd=tmpdir_path)
            assert result.returncode == 0
            run_cli(["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30"], cwd=tmpdir_path)
            run_cli(["note", "add", "2026-06-16", "good day"], cwd=tmpdir_path)

            result = run_cli(
                ["export", "2026-06-16", "--output-dir", str(output_dir)],
                cwd=tmpdir_path,
            )
            assert result.returncode == 0

            md_file = output_dir / "2026-06-16.md"
            assert md_file.exists()

            content = md_file.read_text()
            assert "# 2026-06-16" in content
            assert "## Events" in content
            assert "14:30" in content
            assert "meeting" in content
            assert "## Todos" in content
            assert "write tests" in content
            assert "## Notes" in content
            assert "good day" in content

    def test_export_formats_pending_todo(self):
        """Export renders pending todo as '- [ ] text'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)
            run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=tmpdir_path)

            run_cli(["export", "2026-06-16", "--output-dir", str(output_dir)], cwd=tmpdir_path)

            md_file = output_dir / "2026-06-16.md"
            content = md_file.read_text()
            assert "- [ ] task" in content

    def test_export_formats_completed_todo(self):
        """Export renders completed todo as '- [x] text'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)
            result = run_cli(["todo", "add", "task", "--date", "2026-06-16"], cwd=tmpdir_path)
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            run_cli(["todo", "complete", "--id", todo_id], cwd=tmpdir_path)

            run_cli(["export", "2026-06-16", "--output-dir", str(output_dir)], cwd=tmpdir_path)

            md_file = output_dir / "2026-06-16.md"
            content = md_file.read_text()
            assert "- [x] task" in content

    def test_export_formats_abandoned_todo(self):
        """Export renders abandoned todo as '- [ ] ~~text~~'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)
            result = run_cli(["todo", "add", "old task", "--date", "2026-06-16"], cwd=tmpdir_path)
            assert result.returncode == 0

            # Extract ID
            match = re.search(r"\[(t[a-z0-9]+)\]", result.stdout)
            assert match is not None
            todo_id = match.group(1)

            run_cli(["todo", "abandon", "--id", todo_id], cwd=tmpdir_path)

            run_cli(["export", "2026-06-16", "--output-dir", str(output_dir)], cwd=tmpdir_path)

            md_file = output_dir / "2026-06-16.md"
            content = md_file.read_text()
            assert "- [ ] ~~old task~~" in content

    def test_export_formats_event_with_details(self):
        """Export renders event details as indented lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)
            run_cli(
                ["event", "add", "meeting", "--date", "2026-06-16", "--time", "14:30", "--detail", "discussed project"],
                cwd=tmpdir_path,
            )

            run_cli(["export", "2026-06-16", "--output-dir", str(output_dir)], cwd=tmpdir_path)

            md_file = output_dir / "2026-06-16.md"
            content = md_file.read_text()
            assert "14:30 meeting" in content
            assert "    discussed project" in content


class TestExportAll:
    """Tests for export-all command."""

    def test_export_all_creates_multiple_files(self):
        """Tracer bullet: timeline-cli export-all creates all markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)
            run_cli(["todo", "add", "task A", "--date", "2026-06-16"], cwd=tmpdir_path)
            run_cli(["todo", "add", "task B", "--date", "2026-06-17"], cwd=tmpdir_path)

            result = run_cli(["export-all", "--output-dir", str(output_dir)], cwd=tmpdir_path)
            assert result.returncode == 0

            assert (output_dir / "2026-06-16.md").exists()
            assert (output_dir / "2026-06-17.md").exists()

    def test_export_all_includes_0000_00_00(self):
        """Export-all includes undated record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)
            run_cli(["todo", "add", "inbox task", "--date", "0000-00-00"], cwd=tmpdir_path)

            run_cli(["export-all", "--output-dir", str(output_dir)], cwd=tmpdir_path)

            assert (output_dir / "0000-00-00.md").exists()
