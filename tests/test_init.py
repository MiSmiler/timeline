"""Tests for init command (#8)."""

import json
import os
import tempfile
from pathlib import Path

from conftest import run_cli


def test_init_creates_file():
    """Tracer bullet: timeline-cli init creates timelines.jsonl."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_cli(["init"], cwd=Path(tmpdir))
        assert result.returncode == 0
        assert "Created timelines.jsonl" in result.stdout

        storage_file = Path(tmpdir) / "timelines.jsonl"
        assert storage_file.exists()

        content = storage_file.read_text().strip().split("\n")
        header = json.loads(content[0])
        assert header["schema_version"] == 1


def test_init_fails_if_file_exists():
    """timeline-cli init should fail if timelines.jsonl already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_file = Path(tmpdir) / "timelines.jsonl"
        storage_file.write_text(json.dumps({"schema_version": 1}))

        result = run_cli(["init"], cwd=Path(tmpdir))
        assert result.returncode != 0
        assert "already exists" in result.stderr


def test_init_creates_empty_timeline():
    """Init should create a timeline with no records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_cli(["init"], cwd=Path(tmpdir))

        storage_file = Path(tmpdir) / "timelines.jsonl"
        content = storage_file.read_text().strip().split("\n")

        # Should only have header, no data lines
        assert len(content) == 1