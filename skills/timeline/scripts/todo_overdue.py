#!/usr/bin/env python3
"""
提取过期和无时间的 todo，用于每小时扫描的 cron job。

用法：python3 todo_overdue.py [当前时间 YYYY-MM-DD HH:MM]
示例：python3 todo_overdue.py 2026-06-12 15:30

行为：
- 扫描 timeline/ 下所有 .md 文件
- 提取两类 todo：
  1. 过期 todo：日期已过，或日期相同但时间已过
  2. 无时间 todo：任何日期文件中的无时间条目
- 有则输出，无则静默（空输出）
"""

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def find_timeline_dir():
    """查找 timeline 目录。"""
    if os.path.isdir("timeline"):
        return "timeline"
    parent = os.getcwd()
    while parent != "/":
        timeline_path = os.path.join(parent, "timeline")
        if os.path.isdir(timeline_path):
            return timeline_path
        parent = os.path.dirname(parent)
    return None


def parse_filename_date(filename):
    """从文件名解析日期，返回 (year, month, day) 或 None。"""
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})\.md$", filename)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None


def extract_todos(filepath):
    """提取文件中所有未完成的 todo。返回 [(time_str_or_None, description, line_number), ...]"""
    todos = []
    in_todos_section = False

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "## Todos":
            in_todos_section = True
            continue
        elif stripped.startswith("## ") and stripped != "## Todos":
            in_todos_section = False
            continue

        if not in_todos_section:
            continue

        if stripped.startswith("- [ ]"):
            content = stripped[5:].strip()
            time_match = re.match(r"^(\d{1,2}:\d{2})\s+(.+)$", content)
            if time_match:
                time_str = time_match.group(1)
                if len(time_str) == 4:
                    time_str = "0" + time_str
                todos.append((time_str, time_match.group(2), i + 1))
            else:
                # 无时间的 todo
                todos.append((None, content, i + 1))

    return todos


def main():
    # 解析当前时间
    if len(sys.argv) >= 3:
        now_date_str = sys.argv[1]
        now_time_str = sys.argv[2]
        # 补零
        parts = now_time_str.split(":")
        now_time_str = f"{int(parts[0]):02d}:{int(parts[1]):02d}"
        now_date = datetime.strptime(now_date_str, "%Y-%m-%d").date()
        now_time = now_time_str
    else:
        now = datetime.now()
        now_date = now.date()
        now_time = f"{now.hour:02d}:{now.minute:02d}"

    now_date_tuple = (now_date.year, now_date.month, now_date.day)

    timeline_dir = find_timeline_dir()
    if not timeline_dir:
        print("错误: 未找到 timeline 目录", file=sys.stderr)
        sys.exit(1)

    overdue_todos = []  # (filename, time, description)
    no_time_todos = []  # (filename, description)

    for filename in sorted(os.listdir(timeline_dir)):
        if not filename.endswith(".md"):
            continue

        file_date_tuple = parse_filename_date(filename)
        if file_date_tuple is None:
            continue

        # 跳过 0000-00-00.md（无日期待办单独处理）
        if file_date_tuple == (0, 0, 0):
            filepath = os.path.join(timeline_dir, filename)
            todos = extract_todos(filepath)
            for time_str, desc, _ in todos:
                if time_str is None:
                    no_time_todos.append((filename, desc))
            continue

        file_date = datetime(file_date_tuple[0], file_date_tuple[1], file_date_tuple[2]).date()
        filepath = os.path.join(timeline_dir, filename)
        todos = extract_todos(filepath)

        for time_str, desc, _ in todos:
            if time_str is None:
                # 无时间 todo
                no_time_todos.append((filename, desc))
            else:
                # 有时间 todo：检查是否过期
                if file_date < now_date:
                    # 日期已过
                    overdue_todos.append((filename, time_str, desc))
                elif file_date == now_date and time_str < now_time:
                    # 今天且时间已过
                    overdue_todos.append((filename, time_str, desc))

    # 输出
    if overdue_todos:
        print(f"📋 过期待办（{len(overdue_todos)}条）：")
        for filename, time_str, desc in overdue_todos:
            date_part = filename.replace(".md", "")
            print(f"  - {date_part} {time_str} {desc}")
        print()

    if no_time_todos:
        print(f"📋 无时间待办（{len(no_time_todos)}条）：")
        for filename, desc in no_time_todos:
            print(f"  - {desc}")

    # 如果都没有，静默退出（空输出）


if __name__ == "__main__":
    main()
