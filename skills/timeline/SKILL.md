---
name: timeline
description: "Data format, operation semantics, and integrity constraints for timeline markdown files. Defines file structure, Todo/Event/Note schemas, CRUD semantics, query capabilities, and validation rules."
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

## 操作语义

以下定义适用于所有 Agent 平台的操作含义和行为约定。

### Todo 操作

#### 创建 Todo
在指定日期文件的 `## Todos` 章节添加新条目。可包含时间和/或详情。
- 有时间的 Todo：`- [ ] HH:MM 描述`
- 无时间的 Todo：`- [ ] 描述`
- 约束：`0000-00-00.md` 中的 Todo 不允许有时间前缀

#### 完成 Todo
将 Todo 状态从 `[ ]` 改为 `[x]`。
- 推荐：同时创建 Event 记录完成时间
- 推荐理由：Event 提供完成时间追溯

#### 放弃 Todo
给 Todo 描述添加删除线：`- [ ] ~~描述~~`。
- 表示 Todo 不再执行，但保留记录
- 与删除的区别：放弃保留条目，删除则移除

#### 移动 Todo
更改 Todo 的日期和/或时间。
- 从原文件的 `## Todos` 中移除条目
- 在目标文件的 `## Todos` 中添加条目

#### 编辑 Todo
修改 Todo 的时间和/或描述。
- 时间变更：更新 `HH:MM` 前缀
- 描述变更：更新描述文本
- 详情变更：追加或修改缩进详情行

#### 删除 Todo
从文件中完全移除 Todo 条目（包括详情行）。
- **删除前需确认**
- 与放弃的区别：删除不留痕迹

#### 补充 Todo 详情
在 Todo 条目下追加缩进详情行。
- 格式：4 空格缩进，`- 内容` 或自由文本
- 可多次追加

### Event 操作

#### 创建 Event
在指定日期文件的 `## Events` 章节添加新条目。
- 格式：`- HH:MM 描述。`
- 必须有时间前缀
- 主句精简，细节可折叠到缩进详情
- 如果是未来承诺的事件，推荐询问是否创建对应 Todo

#### 编辑 Event
修改 Event 的时间和/或描述。

#### 删除 Event
从文件中完全移除 Event 条目（包括详情行）。
- **删除前需确认**

#### 补充 Event 详情
在 Event 条目下追加缩进详情行。

---

## 查询能力

以下脚本可用于提升查询效率：

| 脚本 | 功能 |
|-----|------|
| `scripts/todo_list.py` | 列出所有未完成待办 |
| `scripts/todo_by_time.py` | 按时间提取待办 |
| `scripts/todo_overdue.py` | 提取过期和无时间待办 |

Agent 可直接读取文件进行查询，或使用上述脚本提升效率。

---

## 数据校验

修改数据后，可使用以下脚本验证格式规范：

- `scripts/doctor.py` — 验证数据格式，支持 `--fix` 自动修复