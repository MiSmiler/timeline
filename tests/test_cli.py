"""Tests for CLI entry point (#7 skeleton tests)."""

import subprocess
import sys

from conftest import run_cli


def test_cli_help_shows_structure(project_root):
    """Tracer bullet: timeline-cli --help shows command structure."""
    result = run_cli(["--help"], cwd=project_root)
    assert result.returncode == 0
    assert "todo" in result.stdout
    assert "event" in result.stdout
    assert "note" in result.stdout


def test_todo_help_shows_subcommands(project_root):
    """timeline-cli todo --help shows subcommands."""
    result = run_cli(["todo", "--help"], cwd=project_root)
    assert result.returncode == 0
    assert "add" in result.stdout
    assert "list" in result.stdout
    assert "complete" in result.stdout


def test_event_help_shows_subcommands(project_root):
    """timeline-cli event --help shows subcommands."""
    result = run_cli(["event", "--help"], cwd=project_root)
    assert result.returncode == 0
    assert "add" in result.stdout
    assert "list" in result.stdout


def test_note_help_shows_subcommands(project_root):
    """timeline-cli note --help shows subcommands."""
    result = run_cli(["note", "--help"], cwd=project_root)
    assert result.returncode == 0
    assert "add" in result.stdout
    assert "show" in result.stdout


def test_installation_with_uv(project_root):
    """Tracer bullet: uv pip install -e works."""
    result = subprocess.run(
        ["uv", "pip", "install", "-e", str(project_root)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_ruff_linting_passes(project_root):
    """ruff linting should pass."""
    result = subprocess.run(
        ["ruff", "check", str(project_root / "src")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0