#!/usr/bin/env python3
"""
Doctor script for timeline markdown files.
Validates format and optionally fixes issues with --fix flag.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def find_user_timelines_data_dir():
    """Find the user's timelines data directory."""
    if os.path.isdir("timelines"):
        return "timelines"
    return None


def extract_time_from_line(line):
    """Extract time prefix from a todo or event line.

    >>> extract_time_from_line('- [ ] 09:30 晨会')
    '09:30'
    >>> extract_time_from_line('- [ ] 9:30 晨会')  # 小时可以一位
    '9:30'
    >>> extract_time_from_line('- [x] 14:00 已完成')
    '14:00'
    >>> print(extract_time_from_line('- [ ] ~~已放弃~~'))  # 无时间，返回 None
    None
    >>> extract_time_from_line('- 10:30 事件记录')
    '10:30'
    >>> print(extract_time_from_line('- [ ] 无时间前缀'))
    None
    >>> print(extract_time_from_line('普通文本行'))
    None
    """
    stripped = line.strip()
    # Todo format: - [ ] HH:MM description or - [ ] description
    if stripped.startswith('- [ ]') or stripped.startswith('- [x]'):
        content = stripped[5:].strip()
        # Remove strikethrough if present
        if content.startswith('~~') and content.endswith('~~'):
            content = content[2:-2]
        match = re.match(r'^(\d{1,2}):(\d{2})\s+', content)
        if match:
            return f"{match.group(1)}:{match.group(2)}"
    # Event format: - HH:MM description
    elif stripped.startswith('- '):
        content = stripped[2:].strip()
        match = re.match(r'^(\d{1,2}):(\d{2})\s+', content)
        if match:
            return f"{match.group(1)}:{match.group(2)}"
    return None


def time_to_sort_key(time_str):
    """Convert time string to sortable key.

    >>> time_to_sort_key('09:30')
    (9, 30)
    >>> time_to_sort_key('14:00')
    (14, 0)
    >>> time_to_sort_key(None)
    (24, 60)
    >>> time_to_sort_key('')
    (24, 60)
    """
    if not time_str:
        return (24, 60)  # No time goes last
    parts = time_str.split(':')
    return (int(parts[0]), int(parts[1]))


def fix_line_issues(line):
    """Fix line-level issues: time format, todo status.

    Note: Strikethrough fix is intentionally NOT implemented here.
    Partial strikethrough (~~text without closing) is ambiguous and
    should be fixed manually by the user.

    >>> fix_line_issues('- [ ] 10.30 晨会\\n')
    '- [ ] 10:30 晨会\\n'
    >>> fix_line_issues('- [X] 已完成\\n')
    '- [x] 已完成\\n'
    >>> fix_line_issues('- [ ] 正常条目\\n')
    '- [ ] 正常条目\\n'
    >>> fix_line_issues('- 版本1.00发布\\n')  # 不修复非时间格式
    '- 版本1.00发布\\n'
    """
    new_line = line

    # Fix time format only in todo/event lines: 10.30 → 10:30
    # Only match at the beginning of content to avoid false positives
    stripped = line.strip()
    if stripped.startswith('- [ ]') or stripped.startswith('- [x]') or stripped.startswith('- '):
        # Extract content part
        if stripped.startswith('- [ ]') or stripped.startswith('- [x]'):
            content = stripped[5:].strip()
        else:
            content = stripped[2:].strip()
        # Remove strikethrough for matching
        if content.startswith('~~') and content.endswith('~~'):
            content = content[2:-2]
        # Match time at the start of content
        match = re.match(r'^(\d{1,2})\.(\d{2})\s+', content)
        if match:
            old_time = f"{match.group(1)}.{match.group(2)}"
            new_time = f"{match.group(1)}:{match.group(2)}"
            new_line = new_line.replace(old_time, new_time, 1)

    # Fix todo status: [X] → [x]
    new_line = re.sub(r'- \[X\]', '- [x]', new_line)

    return new_line


def doctor_file(filepath, filename, fix=False):
    """Run doctor checks on a single file."""
    filename_date = filename[:-3]  # Remove .md
    errors = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse structure
    h1_line = None
    h1_index = None
    sections = {}
    current_section = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            h1_line = line
            h1_index = i
        elif stripped.startswith('## '):
            if current_section:
                sections[current_section]['end'] = i
            current_section = stripped[3:].strip()
            sections[current_section] = {
                'start': i,
                'end': len(lines),
                'lines': []
            }
        elif current_section:
            sections[current_section]['lines'].append(line)

    if current_section:
        sections[current_section]['end'] = len(lines)

    # Special handling for 0000-00-00.md
    if filename_date == '0000-00-00':
        allowed = {'Todos'}
        forbidden = [s for s in sections.keys() if s not in allowed]

        if forbidden:
            errors.append(f"Cannot have {'/'.join(forbidden)} sections (only Todos allowed)")
            # Will remove forbidden sections when writing if fix=True

        # Check timed todos - cannot fix
        if 'Todos' in sections:
            for line in sections['Todos']['lines']:
                stripped = line.strip()
                if stripped.startswith('- [ ]'):
                    content = stripped[5:].strip()
                    if re.match(r'^\d{1,2}:\d{2}\s+', content):
                        errors.append(f"Todo \"{content}\" not allowed to have time prefix")

        if fix and forbidden:
            # Rewrite file with only Todos section
            final_lines = [f"# {filename_date}\n\n", "## Todos\n"]
            if 'Todos' in sections:
                for line in sections['Todos']['lines']:
                    final_lines.append(fix_line_issues(line))
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(final_lines)
            errors.append(f"Fixed: Removed forbidden sections")

        return errors

    # Regular files

    # 1. Check H1
    if h1_line is None:
        errors.append("No H1 header found")
    elif h1_index != 0:
        errors.append(f"H1 not at first line (line {h1_index + 1})")
    else:
        match = re.match(r'^# (\d{4}-\d{2}-\d{2})', h1_line.strip())
        if match and match.group(1) != filename_date:
            errors.append(f"H1 date '{match.group(1)}' != filename date '{filename_date}'")

    # 2. Check required sections
    required = ['Events', 'Todos', 'Notes']
    missing = [s for s in required if s not in sections]
    if missing:
        errors.append(f"Missing sections: {', '.join(missing)}")

    # 3. Check time format
    for i, line in enumerate(lines):
        if re.search(r'(\d{1,2})\.(\d{2})', line):
            errors.append(f"Line {i+1}: Invalid time format (use ':' not '.')")

    # 4. Check todo status
    for i, line in enumerate(lines):
        if re.search(r'- \[X\]', line):
            errors.append(f"Line {i+1}: Invalid todo status '[X]' (use '[x]')")

    # 5. Check sorting in each section
    for section_name, section_data in sections.items():
        timed = []
        untimed = []
        for line in section_data['lines']:
            t = extract_time_from_line(line)
            if t:
                timed.append((t, line))
            else:
                untimed.append(line)
        sorted_timed = sorted(timed, key=lambda x: time_to_sort_key(x[0]))
        if timed != sorted_timed:
            errors.append(f"{section_name}: Entries not sorted by time")

    # Apply fixes if requested
    if fix and errors:
        final_lines = []

        # H1
        final_lines.append(f"# {filename_date}\n\n")

        # Sections in order
        for section_name in required:
            final_lines.append(f"## {section_name}\n")

            # Get existing section lines or empty
            section_lines = sections.get(section_name, {}).get('lines', [])

            # Fix line issues
            fixed_lines = [fix_line_issues(l) for l in section_lines]

            # Sort by time
            timed = []
            untimed = []
            for line in fixed_lines:
                t = extract_time_from_line(line)
                if t:
                    timed.append((t, line))
                else:
                    untimed.append(line)

            sorted_timed = sorted(timed, key=lambda x: time_to_sort_key(x[0]))
            for _, line in sorted_timed:
                final_lines.append(line)
            for line in untimed:
                final_lines.append(line)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)

        # Convert errors to "Fixed" messages
        fixed_errors = []
        if h1_line is None or h1_index != 0:
            fixed_errors.append("Fixed: H1 header")
        if h1_line and re.match(r'^# (\d{4}-\d{2}-\d{2})', h1_line.strip()):
            match = re.match(r'^# (\d{4}-\d{2}-\d{2})', h1_line.strip())
            if match and match.group(1) != filename_date:
                fixed_errors.append("Fixed: H1 date")
        if missing:
            fixed_errors.append("Fixed: Missing sections")
        if any(re.search(r'(\d{1,2})\.(\d{2})', l) for l in lines):
            fixed_errors.append("Fixed: Time format")
        if any(re.search(r'- \[X\]', l) for l in lines):
            fixed_errors.append("Fixed: Todo status")
        for section_name in sections:
            timed = [(extract_time_from_line(l), l) for l in sections[section_name]['lines'] if extract_time_from_line(l)]
            if timed != sorted(timed, key=lambda x: time_to_sort_key(x[0])):
                fixed_errors.append(f"Fixed: {section_name} sorting")

        return fixed_errors

    return errors


def main():
    parser = argparse.ArgumentParser(
        description='Doctor script for timeline markdown files.'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically fix fixable issues.'
    )
    args = parser.parse_args()

    timeline_dir = find_user_timelines_data_dir()

    if not timeline_dir:
        print("Error: timelines directory not found", file=sys.stderr)
        sys.exit(1)

    all_errors = []
    fixed_count = 0
    unfixable_count = 0
    checked = 0

    for filename in sorted(os.listdir(timeline_dir)):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(timeline_dir, filename)
        checked += 1

        errors = doctor_file(filepath, filename, args.fix)

        for error in errors:
            if 'Fixed' in error:
                fixed_count += 1
            else:
                unfixable_count += 1
            all_errors.append(f"{filename}: {error}")

    if not checked:
        print("No markdown files found in timelines directory.")
        return

    if all_errors:
        print("Issues found:\n")
        for error in all_errors:
            print(f"  - {error}")

        if args.fix:
            print(f"\n✅ Fixed {fixed_count} issue(s), {unfixable_count} unfixable.")
        else:
            print(f"\n{len(all_errors)} issue(s) found. Run with --fix to auto-fix fixable issues.")
        sys.exit(1 if unfixable_count > 0 else 0)
    else:
        print(f"✅ All checks passed: {checked} file(s) validated.")


if __name__ == '__main__':
    main()