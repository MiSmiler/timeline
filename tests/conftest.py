"""Test fixtures for timeline-cli tests."""

import json
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


def read_items_from_storage(storage_file: Path) -> dict[str, list[dict]]:
    """Read items from .timelines.jsonl and group by type.

    Returns dict with keys: 'events', 'todos', 'notes'.
    Each value is a list of items (dict).
    """
    content = storage_file.read_text().strip().split("\n")

    items_by_type: dict[str, list[dict]] = {"events": [], "todos": [], "notes": []}

    for line in content[1:]:  # Skip header
        if line.strip():
            item = json.loads(line)
            item_type = item.get("type")
            if item_type == "event":
                items_by_type["events"].append(item)
            elif item_type == "todo":
                items_by_type["todos"].append(item)
            elif item_type == "note":
                items_by_type["notes"].append(item)

    return items_by_type


def read_items_by_date(storage_file: Path, date: str | None) -> dict[str, list[dict]]:
    """Read items from .timelines.jsonl and group by type for a specific date.

    Args:
        storage_file: Path to data.jsonl
        date: Date string (YYYY-MM-DD) or None for undated items

    Returns dict with keys: 'events', 'todos', 'notes'.
    Each value is a list of items (dict) matching the date.
    """
    items_by_type = read_items_from_storage(storage_file)

    result: dict[str, list[dict]] = {"events": [], "todos": [], "notes": []}
    for type_key, items in items_by_type.items():
        for item in items:
            if item.get("date") == date:
                result[type_key].append(item)

    return result
