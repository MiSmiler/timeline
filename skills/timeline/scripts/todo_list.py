#!/usr/bin/env python3
"""
List all uncompleted todos from timeline markdown files.
"""

import os
import re
import sys
from pathlib import Path


def find_user_timelines_data_dir():
    """Find the user's timelines data directory."""
    if os.path.isdir("timelines"):
        return "timelines"
    return None


def parse_todo_line(line):
    """Parse a todo line and return (time, description, detail_lines) or None."""
    # Match: - [ ] HH:MM description or - [ ] description
    # Also match strikethrough abandoned todos
    match = re.match(r'^- \[ \] (?:~~)?(.+?)(?:~~)?$', line.strip())
    if not match:
        return None

    content = match.group(1).strip()

    # Check if it has time prefix
    time_match = re.match(r'^(\d{1,2}:\d{2})\s+(.+)$', content)
    if time_match:
        return (time_match.group(1), time_match.group(2))

    return (None, content)


def parse_file(filepath):
    """Parse a markdown file and extract uncompleted todos."""
    todos = []
    in_todos_section = False
    current_todo = None
    detail_lines = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for section headers
        if stripped == '## Todos':
            in_todos_section = True
            continue
        elif stripped.startswith('## ') and stripped != '## Todos':
            in_todos_section = False
            continue

        if not in_todos_section:
            continue

        # Check for todo item
        if stripped.startswith('- [ ]'):
            # Save previous todo if exists
            if current_todo:
                todos.append({
                    'time': current_todo[0],
                    'description': current_todo[1],
                    'detail': '\n'.join(detail_lines) if detail_lines else None,
                    'line_number': i + 1
                })

            current_todo = parse_todo_line(stripped)
            detail_lines = []

        # Check for detail (indented with 4 spaces or tab)
        elif current_todo and (line.startswith('    ') or line.startswith('\t')):
            # Remove leading whitespace
            detail_content = stripped.lstrip('- ').strip()
            if detail_content:
                detail_lines.append(detail_content)

    # Don't forget the last todo
    if current_todo:
        todos.append({
            'time': current_todo[0],
            'description': current_todo[1],
            'detail': '\n'.join(detail_lines) if detail_lines else None,
            'line_number': -1  # Will be set correctly above
        })

    return todos


def main():
    timeline_dir = find_user_timelines_data_dir()

    if not timeline_dir:
        print("Error: timelines directory not found", file=sys.stderr)
        sys.exit(1)

    all_todos = {}  # filename -> [todos]

    # Find all markdown files
    for filename in sorted(os.listdir(timeline_dir)):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(timeline_dir, filename)
        todos = parse_file(filepath)

        if todos:
            all_todos[filename] = todos

    if not all_todos:
        print("No uncompleted todos found.")
        return

    # Output format
    total_count = 0
    for filename, todos in all_todos.items():
        print(f"\n📄 {filename}")
        for todo in todos:
            total_count += 1
            time_str = f"{todo['time']} " if todo['time'] else ""
            status = "❌" if "~~" in todo['description'] else "⬜"
            print(f"  - [ ] {time_str}{todo['description']}")
            if todo['detail']:
                for detail_line in todo['detail'].split('\n'):
                    print(f"      - {detail_line}")

    print(f"\n📊 Total: {total_count} uncompleted todo(s)")


if __name__ == '__main__':
    main()