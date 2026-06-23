"""Tests for init command (#8)."""

import json
import tempfile
from pathlib import Path

from conftest import run_cli


def test_init_creates_file():
    """Tracer bullet: timeline-cli init creates .timeline/data.jsonl."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_cli(["init"], cwd=Path(tmpdir))
        assert result.returncode == 0
        assert "Created .timeline/data.jsonl" in result.stdout

        storage_file = Path(tmpdir) / ".timeline" / "data.jsonl"
        assert storage_file.exists()

        content = storage_file.read_text().strip().split("\n")
        header = json.loads(content[0])
        assert header["schema_version"] == 1


def test_init_fails_if_file_exists():
    """timeline-cli init should fail if .timeline/data.jsonl already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        timeline_dir = Path(tmpdir) / ".timeline"
        timeline_dir.mkdir()
        storage_file = timeline_dir / "data.jsonl"
        storage_file.write_text(json.dumps({"schema_version": 1}))

        result = run_cli(["init"], cwd=Path(tmpdir))
        assert result.returncode != 0
        assert "Timeline already initialized" in result.stderr


def test_init_creates_empty_timeline():
    """Init should create a timeline with no records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_cli(["init"], cwd=Path(tmpdir))

        storage_file = Path(tmpdir) / ".timeline" / "data.jsonl"
        content = storage_file.read_text().strip().split("\n")

        # Should only have header, no data lines
        assert len(content) == 1
