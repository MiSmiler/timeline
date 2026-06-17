"""Test fixtures for timeline-cli tests."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for a test project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_dir)


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def run_cli(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run timeline-cli with given arguments via Python module."""
    # Get project root and add src to PYTHONPATH
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path)

    # Use python -m to run without needing pip install
    return subprocess.run(
        [sys.executable, "-m", "timeline_cli.cli"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )
