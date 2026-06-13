---
name: timeline
description: "Data format and integrity constraints for timeline markdown files. Defines file structure, Todo/Event/Note schemas, and validation rules."
tags: []
related_skills: []
---

# Timeline 数据格式

定义 timeline markdown 文件的数据格式和完整性约束。

## 文件结构

### 文件位置与命名

- 目录：`timelines/`
- 文件名格式：`YYYY-MM-DD.md`（如 `2026-06-12.md`）
- 无日期待办文件：`0000-00-00.md`

### 文件模板

普通日期文件：
```markdown
# YYYY-MM-DD

## Events

## Todos

## Notes
```

无日期文件（`0000-00-00.md`）：
```markdown
# 0000-00-00

## Todos
```

**约束**：`0000-00-00.md` 只允许 `## Todos` 章节，不允许 Events 和 Notes。

### 文件不存在处理

当操作的目标文件不存在时，使用标准模板创建：
- 普通日期文件：包含 Events、Todos、Notes 三个章节
- `0000-00-00.md`：只包含 Todos 章节

---

## 数据格式

### Events（事件）

- 格式：`- HH:MM 描述。`
- 必须有时间前缀
- 表示在特定时刻发生的事情
- 支持详情（缩进 4 空格）：
```markdown
- 14:30 和客户开会。
    - 讨论了项目时间线。
```

### Todos（待办）

- 格式：`- [ ] HH:MM 描述`（有时间）或 `- [ ] 描述`（无时间）
- 状态标记：
  - `[ ]` - 未完成
  - `[x]` - 已完成
  - `[ ] ~~描述~~` - 已放弃（删除线）
- 支持详情：
```markdown
- [ ] 15:00 收拾桌面
    - 扔掉过期零食。
```

**约束**：`0000-00-00.md` 中的 Todo 不允许有时间前缀。

### Notes（笔记）

- 自由格式文本，记录想法、目标、心情等
- 无特定格式要求

---

## 排序规则

每个章节内：
- 有时间的条目按时间升序排序
- 无时间的条目排在最后

---

## 辅助脚本

位于 `scripts/` 目录，用于数据校验和查询：

- `doctor.py`：验证数据格式，支持 `--fix` 自动修复
- `todo_list.py`：列出所有未完成待办
- `todo_by_time.py`：按时间提取待办
- `todo_overdue.py`：提取过期和无时间待办