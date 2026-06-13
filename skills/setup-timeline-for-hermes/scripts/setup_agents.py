#!/usr/bin/env python3
"""Inject timeline usage rules into a project's AGENTS.md.

Usage:
    python3 setup_agents.py [target_dir]

target_dir defaults to the current working directory.

The script reads the template from templates/AGENTS.md (relative to this
script's directory) and injects it into target_dir/AGENTS.md wrapped in
marker comments.  Re-running the script replaces the content between
markers (idempotent).
"""

import sys
from pathlib import Path

MARKER_START = "<!-- timeline-setup-start -->"
MARKER_END = "<!-- timeline-setup-end -->"


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    template_path = script_dir.parent / "templates" / "AGENTS_TEMPLATE.md"

    if not template_path.exists():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    template_content = template_path.read_text(encoding="utf-8").rstrip("\n")
    wrapped = f"{MARKER_START}\n{template_content}\n{MARKER_END}"

    # Determine target directory
    target_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    agents_path = target_dir / "AGENTS.md"

    # Create timelines/ data directory
    timeline_dir = target_dir / "timelines"
    timeline_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured directory: {timeline_dir}")

    # Inject into AGENTS.md
    if agents_path.exists():
        existing = agents_path.read_text(encoding="utf-8")
        if MARKER_START in existing and MARKER_END in existing:
            # Replace existing marker region
            pre = existing[: existing.index(MARKER_START)]
            post = existing[existing.index(MARKER_END) + len(MARKER_END) :]
            new_content = f"{pre}{wrapped}{post}".rstrip("\n") + "\n"
            agents_path.write_text(new_content, encoding="utf-8")
            print(f"Updated AGENTS.md (replaced marker region): {agents_path}")
        else:
            # Append with a blank line separator
            new_content = existing.rstrip("\n") + f"\n\n{wrapped}\n"
            agents_path.write_text(new_content, encoding="utf-8")
            print(f"Appended to AGENTS.md: {agents_path}")
    else:
        # Create new file
        agents_path.write_text(f"{wrapped}\n", encoding="utf-8")
        print(f"Created AGENTS.md: {agents_path}")


if __name__ == "__main__":
    main()
