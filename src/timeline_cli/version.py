"""Version utilities for timeline-cli."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def get_version() -> str:
    """Get the version of timeline-cli.

    First tries to read from installed package metadata.
    If not found (e.g., running in development mode without installation),
    falls back to reading pyproject.toml directly.

    Returns:
        The version string.
    """
    try:
        return version("timeline-cli")
    except PackageNotFoundError:
        # Fallback for development mode: read from pyproject.toml
        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            for line in content.splitlines():
                if line.startswith("version = "):
                    return line.split('"')[1]
        return "unknown"
