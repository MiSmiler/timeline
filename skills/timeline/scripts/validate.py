#!/usr/bin/env python3
"""
Validate that H1 date matches filename in timeline markdown files.
"""

import os
import re
import sys
from pathlib import Path


def find_timeline_dir():
    """Find the timeline directory."""
    if os.path.isdir("timeline"):
        return "timeline"
    parent = os.getcwd()
    while parent != "/":
        timeline_path = os.path.join(parent, "timeline")
        if os.path.isdir(timeline_path):
            return timeline_path
        parent = os.path.dirname(parent)
    return None


def extract_h1_date(filepath):
    """Extract the date from H1 header."""
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('# '):
                # Extract date from "# YYYY-MM-DD"
                match = re.match(r'^# (\d{4}-\d{2}-\d{2})$', line)
                if match:
                    return match.group(1)
                # Also allow "# YYYY-MM-DD" with other text
                match = re.match(r'^# (\d{4}-\d{2}-\d{2})', line)
                if match:
                    return match.group(1)
                return line[2:]  # Return whatever is after "# "
            if line and not line.startswith('#'):
                break
    return None


def validate_undated_file(filepath, filename):
    """Validate 0000-00-00.md: only ## Todos allowed, no timed todos."""
    errors = []
    sections = []
    timed_todos = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_todos_section = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('## '):
            section_name = stripped[3:].strip()
            sections.append(section_name)
            in_todos_section = (section_name == 'Todos')
            continue
        if in_todos_section and stripped.startswith('- [ ]'):
            content = stripped[5:].strip()
            if re.match(r'^\d{1,2}:\d{2}\s+', content):
                timed_todos.append((i + 1, content))

    # Check: only ## Todos section allowed
    allowed = {'Todos'}
    forbidden = [s for s in sections if s not in allowed]
    if forbidden:
        errors.append(f"{filename}: 不能有 {'/'.join(forbidden)} 章节（仅允许 Todos）")

    # Check: no timed todos
    for line_no, content in timed_todos:
        errors.append(f"{filename}: Todo \"{content}\" 不允许有时间前缀（line {line_no}）")

    return errors


def main():
    timeline_dir = find_timeline_dir()
    if not timeline_dir:
        print("Error: timeline directory not found", file=sys.stderr)
        sys.exit(1)

    errors = []
    checked = 0

    for filename in sorted(os.listdir(timeline_dir)):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(timeline_dir, filename)
        filename_date = filename[:-3]  # Remove .md
        checked += 1

        # Validate 0000-00-00.md special rules
        if filename_date == '0000-00-00':
            errors.extend(validate_undated_file(filepath, filename))
            continue

        # Standard: H1 date must match filename
        h1_date = extract_h1_date(filepath)
        if h1_date is None:
            errors.append(f"{filename}: No H1 header found")
        elif h1_date != filename_date:
            errors.append(f"{filename}: H1 date '{h1_date}' != filename date '{filename_date}'")

    if not checked:
        print("No markdown files found in timeline directory.")
        return

    if errors:
        print("❌ Validation failed:\n")
        for error in errors:
            print(f"  - {error}")
        print(f"\n{len(errors)} error(s) found in {checked} file(s).")
        sys.exit(1)
    else:
        print(f"✅ Validation passed: {checked} file(s) checked.")


if __name__ == '__main__':
    main()