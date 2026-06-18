"""Tests to verify export and export-all commands have been removed (issue #53)."""

import tempfile
from pathlib import Path

from conftest import run_cli


class TestExportCommandRemoved:
    """Tests verifying export command is removed."""

    def test_export_command_returns_error(self):
        """After removal, export command should return error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)

            result = run_cli(
                ["export", "2026-06-16", "--output-dir", str(output_dir)],
                cwd=tmpdir_path,
            )

            # Command should fail (exit code != 0)
            assert result.returncode != 0
            # Error message should indicate unknown command or similar
            assert (
                "error" in result.stderr.lower()
                or "unknown" in result.stderr.lower()
                or "invalid" in result.stderr.lower()
            )


class TestExportAllCommandRemoved:
    """Tests verifying export-all command is removed."""

    def test_export_all_command_returns_error(self):
        """After removal, export-all command should return error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "exported"
            output_dir.mkdir()

            run_cli(["init"], cwd=tmpdir_path)

            result = run_cli(
                ["export-all", "--output-dir", str(output_dir)],
                cwd=tmpdir_path,
            )

            # Command should fail (exit code != 0)
            assert result.returncode != 0
            # Error message should indicate unknown command or similar
            assert (
                "error" in result.stderr.lower()
                or "unknown" in result.stderr.lower()
                or "invalid" in result.stderr.lower()
            )
