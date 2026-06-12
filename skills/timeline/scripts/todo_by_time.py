#!/usr/bin/env python3
"""
按日期和时间提取 todo，用于定时提醒的 cron job。

用法：python3 todo_by_time.py [YYYY-MM-DD HH:MM]
示例：python3 todo_by_time.py 2026-06-12 15:00

行为：
- 不传参数：使用当前日期和时间（适合 no_agent cron job 直接调用）
- 传参数：使用指定的日期和时间
- 读取 timelines/YYYY-MM-DD.md
- 提取时间匹配 HH:MM 的未完成 todo
- 有则输出，无则静默（空输出）
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path


def find_user_timelines_data_dir():
    """查找 timelines 目录。"""
    if os.path.isdir("timelines"):
        return "timelines"
    return None


def extract_todos_by_time(filepath, target_time):
    """提取指定时间的未完成 todo。"""
    todos = []
    in_todos_section = False

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 检查章节标题
        if stripped == "## Todos":
            in_todos_section = True
            continue
        elif stripped.startswith("## ") and stripped != "## Todos":
            in_todos_section = False
            continue

        if not in_todos_section:
            continue

        # 匹配未完成的 todo：- [ ] HH:MM 描述
        if stripped.startswith("- [ ]"):
            content = stripped[5:].strip()
            time_match = re.match(r"^(\d{1,2}:\d{2})\s+(.+)$", content)
            if time_match:
                time_str = time_match.group(1)
                # 补零对齐：9:00 -> 09:00
                if len(time_str) == 4:
                    time_str = "0" + time_str
                if time_str == target_time:
                    desc = time_match.group(2)
                    # 收集缩进的详情行
                    details = []
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j]
                        if next_line.startswith("    ") or next_line.startswith("\t"):
                            detail = next_line.strip().lstrip("- ").strip()
                            if detail:
                                details.append(detail)
                        else:
                            break
                    todos.append({"description": desc, "details": details})

    return todos


def main():
    if len(sys.argv) >= 3:
        target_date = sys.argv[1]
        target_time = sys.argv[2]
    else:
        # 不传参数时使用当前时间（适合 no_agent cron job）
        now = datetime.now()
        target_date = now.strftime("%Y-%m-%d")
        target_time = now.strftime("%H:%M")

    # 补零：15:0 -> 15:00，9:5 -> 09:05
    parts = target_time.split(":")
    if len(parts) == 2:
        target_time = f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    timeline_dir = find_user_timelines_data_dir()

    if not timeline_dir:
        print("错误: 未找到 timelines 目录", file=sys.stderr)
        sys.exit(1)

    filepath = os.path.join(timeline_dir, f"{target_date}.md")
    if not os.path.exists(filepath):
        # 文件不存在，静默退出
        return

    todos = extract_todos_by_time(filepath, target_time)

    if not todos:
        # 无匹配 todo，静默退出
        return

    # 输出匹配的 todo
    for todo in todos:
        print(f"- [ ] {target_time} {todo['description']}")
        for detail in todo["details"]:
            print(f"    - {detail}")


if __name__ == "__main__":
    main()
