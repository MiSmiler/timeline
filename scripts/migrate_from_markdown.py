"""Migration script to convert markdown files to jsonline format.

Usage:
    python scripts/migrate_from_markdown.py <directory>

Converts all YYYY-MM-DD.md and 0000-00-00.md files in the directory
to a single timelines.jsonl file.
"""

import json
import re
import sys
from pathlib import Path


def parse_markdown_file(md_path: Path) -> dict:
    """Parse a markdown file and return a daily record dict."""
    content = md_path.read_text()

    # Extract date from filename
    filename = md_path.name
    if not (re.match(r"\d{4}-\d{2}-\d{2}.md$", filename) or filename == "0000-00-00.md"):
        raise ValueError(f"Invalid filename: {filename}")

    date = filename.replace(".md", "")

    # Parse sections
    events = []
    todos = []
    notes = None

    lines = content.split("\n")

    current_section = None
    last_event_idx = None  # Track last event for details
    last_todo_idx = None  # Track last todo for details
    for line in lines:
        # Section headers
        if line.startswith("## Events"):
            current_section = "events"
            continue
        elif line.startswith("## Todos"):
            current_section = "todos"
            continue
        elif line.startswith("## Notes"):
            current_section = "notes"
            continue

        # Parse indented details (4 spaces, possibly with "- " prefix)
        if line.startswith("    ") and line.strip():
            detail_text = line.strip()
            # Remove "- " prefix if present
            if detail_text.startswith("- "):
                detail_text = detail_text[2:]

            # Add to last event or todo
            if current_section == "events" and last_event_idx is not None:
                events[last_event_idx]["details"].append(detail_text)
                continue
            elif current_section == "todos" and last_todo_idx is not None:
                todos[last_todo_idx]["details"].append(detail_text)
                continue

        # Parse events
        if current_section == "events" and line.startswith("- "):
            # Format: "- HH:MM Description. Details..."
            # line[2:] is "HH:MM Description. Details..."
            match = re.match(r"(\d{2}:\d{2}) (.+)", line[2:])
            if match:
                time = match.group(1)
                text = match.group(2)
                # Split into text and details (first sentence is text)
                parts = text.split(". ", 1)
                event_text = parts[0]
                details = [parts[1]] if len(parts) > 1 else []
                events.append(
                    {
                        "time": time,
                        "text": event_text,
                        "details": details,
                    }
                )
                last_event_idx = len(events) - 1

        # Parse todos
        if current_section == "todos" and line.startswith("- "):
            # Format: "- [ ] Description" or "- [x] Description" or "- [ ] ~~Description~~"
            # Format: "- [ ] HH:MM Description" (time optional)
            # line[2:] is "[ ] Description" or "[x] Description"
            match = re.match(r"\[([ x])\] (.+)", line[2:])
            if match:
                checked = match.group(1)
                text = match.group(2)

                # Check for abandoned (~~text~~)
                abandoned_match = re.match(r"~~(.+)~~", text)
                if abandoned_match:
                    status = "abandoned"
                    text = abandoned_match.group(1)
                elif checked == "x":
                    status = "completed"
                else:
                    status = "pending"

                # Check for time prefix (HH:MM)
                time_match = re.match(r"(\d{2}:\d{2}) (.+)", text)
                if time_match:
                    todo_time = time_match.group(1)
                    text = time_match.group(2)
                else:
                    todo_time = None

                todos.append(
                    {
                        "time": todo_time,
                        "text": text,
                        "status": status,
                        "details": [],
                    }
                )
                last_todo_idx = len(todos) - 1

        # Parse notes (everything after ## Notes)
        if current_section == "notes" and line.strip():
            if notes is None:
                notes = line.strip()
            else:
                notes += "\n" + line.strip()

    return {
        "date": date,
        "events": events,
        "todos": todos,
        "notes": notes,
    }


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_from_markdown.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        sys.exit(1)

    # Find all markdown files
    md_files = list(directory.glob("*.md"))
    valid_files = []
    skipped_files = []

    for md_file in md_files:
        if re.match(r"\d{4}-\d{2}-\d{2}.md$", md_file.name) or md_file.name == "0000-00-00.md":
            valid_files.append(md_file)
        else:
            skipped_files.append(md_file)
            print(f"Skipping invalid filename: {md_file.name}")

    if not valid_files:
        print("No valid markdown files found")
        sys.exit(0)

    # Parse all files
    records = []
    for md_file in valid_files:
        try:
            record = parse_markdown_file(md_file)
            records.append(record)
            print(f"Migrated: {md_file.name}")
        except Exception as e:
            print(f"Error parsing {md_file.name}: {e}")
            sys.exit(1)

    # Write output
    output_path = directory / "timelines.jsonl"
    if output_path.exists():
        print(f"Error: {output_path} already exists. Use --overwrite to replace.")
        sys.exit(1)

    # Write header
    lines = [json.dumps({"schema_version": 1})]

    # Sort records by date and write
    records.sort(key=lambda r: r["date"])
    for record in records:
        lines.append(json.dumps(record))

    output_path.write_text("\n".join(lines) + "\n")
    print(f"\nCreated {output_path} with {len(records)} records")


if __name__ == "__main__":
    main()
