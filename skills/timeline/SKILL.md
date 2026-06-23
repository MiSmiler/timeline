---
name: timeline
description: "Manage Todo/Event/Note. Triggers: 待办/任务/todo (Todo ops), 事件/event (Event ops), 我做了/刚刚...了 (create Event), 笔记/note (Note ops), 提醒我做X (create timed Todo), 有什么事做/未完成的 (list pending Todos), 今天/明天的安排 (diary view), 修改时间/加细节 (edit Todo/Event)."
---

# Timeline CLI 操作指南

timeline-cli 是一个基于 JSONL 存储的待办/事件/笔记管理工具。Agent 应通过 CLI 命令操作数据，而非直接操作文件。

---

## 概述

**存储位置**：`.timeline/data.jsonl`

**禁止直接修改**：所有数据操作必须通过 CLI 命令完成。直接编辑 jsonl 文件会绕过验证逻辑，导致数据损坏。

**首次使用**：需运行 `timeline-cli init` 初始化存储

**命令结构**：`timeline-cli <resource> <action> [args]`

**JSON 输出优先**：查询类命令（`todo list`、`event list`）支持 `--json` 参数。Agent 查询数据时应优先使用 `--json`，JSONlines 格式更易于解析和分析。

---

## ID 系统

Todo/Event 的编辑、删除、完成等操作依赖 `--id` 参数定位目标条目。

**Todo ID**：`t` + 5 位随机字符（小写字母 + 数字），如 `t7b3k`

**Event ID**：`e` + 5 位随机字符（小写字母 + 数字），如 `e4x1m`

**Note**：无 ID，通过日期直接定位

**唯一性**：ID 全局唯一，跨日期不重复

---

## `--at` 参数（add/list 命令）

统一时间表达式参数，接受以下格式：

**Timepoint 格式**（单个时间点）：
- `now` — 当前时刻（date + time）
- `YYYY-MM-DD` — 具体日期（如 `2026-06-22`）
- `today` / `yesterday` / `tomorrow` — 相对日期
- `HH:MM` — 时间（默认今天，如 `15:00`）
- `YYYY-MM-DDTHH:MM` — 日期 + 时间（T 分隔符，如 `2026-06-22T14:00`）
- `todayTHH:MM` — 相对日期 + 时间（如 `todayT15:00`）
- `undated` — 无日期（用于 Todo）
- `+2h` / `-30m` / `+2h30m` — 相对偏移（基于 now）

**Timerange 格式**（时间范围）：
- `..` — 所有记录（无边界）
- `today` / `yesterday` / `tomorrow` — 展开为全天范围
- `YYYY-MM-DD..YYYY-MM-DD` — 日期范围
- `..today` / `today..` — 相对范围
- `..now` / `now..` — 相对当前时间
- `YYYY-MM-DDTHH:MM..` — 精确时间点
- `?` — 无日期记录（undated）

### `diary` 命令的日期参数

接受以下格式：
- `YYYY-MM-DD` — 具体日期
- `today` / `yesterday` / `tomorrow` — 相对日期
- 不提供参数时默认为 `today`

---

## Todo 操作

### 添加 Todo

```bash
timeline-cli todo add TEXT --at AT [--detail DETAIL]
```

参数：
- `TEXT` — 必填，待办描述（位置参数）
- `--at AT` — 必填，时间（见「`--at` 参数」章节）
- `--detail DETAIL` — 可选，详情文本

示例：
```bash
# 创建当前时刻的待办
timeline-cli todo add "写单元测试" --at now

# 创建今天的待办（无具体时间）
timeline-cli todo add "开会" --at today

# 创建带时间的待办
timeline-cli todo add "代码评审" --at "2026-06-22T14:00"
timeline-cli todo add "提交报告" --at "15:00"

# 创建相对时间的待办
timeline-cli todo add "休息一下" --at "+2h"

# 创建无日期待办
timeline-cli todo add "有空时整理桌面" --at undated

# 创建带详情的待办
timeline-cli todo add "修复 bug" --at now --detail "用户反馈的登录问题"
```

### 完成 Todo

```bash
timeline-cli todo complete --id ID
```

参数：
- `--id ID` — 必填，Todo ID（如 `t7b3k`）

示例：
```bash
timeline-cli todo complete --id t7b3k
```

### 放弃 Todo

```bash
timeline-cli todo abandon --id ID
```

参数：
- `--id ID` — 必填，Todo ID

放弃保留记录，状态变为 `abandoned`。与删除的区别：放弃保留条目，删除则移除。

示例：
```bash
timeline-cli todo abandon --id t7b3k
```

### 编辑 Todo

```bash
timeline-cli todo edit --id ID [--new-text TEXT] [--new-at AT] \
  [--append-detail TEXT] [--set-detail TEXT]
```

参数：
- `--id ID` — 必填，Todo ID
- `--new-text TEXT` — 可选，更新描述
- `--new-at AT` — 可选，更新时间（见「`--at` 参数」章节，支持 `""` 转为 undated）
- `--append-detail TEXT` — 可选，追加详情
- `--set-detail TEXT` — 可选，覆盖详情（多行用换行分隔）

示例：
```bash
# 更新描述
timeline-cli todo edit --id t7b3k --new-text "写单元测试和集成测试"

# 更新时间
timeline-cli todo edit --id t7b3k --new-at "15:00"

# 转换为 undated
timeline-cli todo edit --id t7b3k --new-at ""

# 追加详情
timeline-cli todo edit --id t7b3k --append-detail "需要 mock 外部 API"

# 覆盖详情（多行）
timeline-cli todo edit --id t7b3k --set-detail "第一行详情
第二行详情"
```

### 删除 Todo

```bash
timeline-cli todo delete --id ID [--yes]
```

参数：
- `--id ID` — 必填，Todo ID
- `--yes` — 可选，跳过确认提示

**删除前需确认**：Agent 应先向用户确认是否删除，确认后使用 `--yes` 参数。

示例：
```bash
# Agent 向用户确认后执行
timeline-cli todo delete --id t7b3k --yes
```

### 查询 Todo

```bash
timeline-cli todo list [--at AT] [--no-time] [--json] [--show-id] \
  [--contains TEXT] [--status STATUS]
```

参数：
- `--at AT` — 时间表达式（见「`--at` 参数」章节）。必填之一。
- `--no-time` — 筛选无时间的 Todo。
- `--json` — 可选，JSONlines 格式输出
- `--show-id` — 可选，在输出中显示 ID
- `--contains TEXT` — 可选，文本子串筛选
- `--status STATUS` — 可选，按状态筛选（`pending`/`completed`/`abandoned`）

**参数要求**：至少提供一个参数（`--at`、`--no-time`、`--status`、`--contains`）。

示例：
```bash
# 查看今日所有待办（JSON 输出，推荐用于 Agent）
timeline-cli todo list --at today --json

# 查看今日待办（markdown 输出，适合展示给用户）
timeline-cli todo list --at today

# 查看过期待办
timeline-cli todo list --at ..now --status pending --json

# 查看无日期待办
timeline-cli todo list --at undated --json

# 查看无时间待办（日期存在但无具体时间）
timeline-cli todo list --at .. --no-time --json

# 文本筛选
timeline-cli todo list --at .. --contains "测试" --json
```

---

## Event 操作

### 添加 Event

```bash
timeline-cli event add TEXT --at AT [--detail DETAIL]
```

参数：
- `TEXT` — 必填，事件描述（位置参数）
- `--at AT` — 必填，时间（见「`--at` 参数」章节）
- `--detail DETAIL` — 可选，详情文本

示例：
```bash
# 记录当前事件
timeline-cli event add "团队会议" --at now

# 记录过去的事件
timeline-cli event add "完成报告" --at "yesterdayT15:00"
timeline-cli event add "提交代码" --at "-2h"

# 记录带详情的事件
timeline-cli event add "发布版本" --at "2026-06-21T10:00" --detail "v1.2.0"
```

### 编辑 Event

```bash
timeline-cli event edit --id ID [--new-text TEXT] [--new-at AT] \
  [--append-detail TEXT] [--set-detail TEXT]
```

参数：
- `--id ID` — 必填，Event ID（如 `e4x1m`）
- `--new-text TEXT` — 可选，更新描述
- `--new-at AT` — 可选，更新时间（见「`--at` 参数」章节）
- `--append-detail TEXT` — 可选，追加详情
- `--set-detail TEXT` — 可选，覆盖详情（多行用换行分隔）

示例：
```bash
# 更新时间
timeline-cli event edit --id e4x1m --new-at "10:00"

# 追加详情
timeline-cli event edit --id e4x1m --append-detail "会议纪录已发送"

# 覆盖详情
timeline-cli event edit --id e4x1m --set-detail "新的详情内容"
```

### 删除 Event

```bash
timeline-cli event delete --id ID [--yes]
```

参数：
- `--id ID` — 必填，Event ID
- `--yes` — 可选，跳过确认提示

**删除前需确认**：Agent 应先向用户确认是否删除，确认后使用 `--yes` 参数。

示例：
```bash
timeline-cli event delete --id e4x1m --yes
```

### 查询 Event

```bash
timeline-cli event list [--at AT] [--json] [--show-id] [--contains TEXT]
```

参数：
- `--at AT` — 时间表达式（见「`--at` 参数」章节）。必填之一。
- `--json` — 可选，JSONlines 格式输出
- `--show-id` — 可选，在输出中显示 ID
- `--contains TEXT` — 可选，文本子串筛选

**参数要求**：至少提供一个参数（`--at` 或 `--contains`）。

示例：
```bash
# 查看今日事件（JSON 输出，推荐用于 Agent）
timeline-cli event list --at today --json

# 查看今日事件（markdown 输出，适合展示给用户）
timeline-cli event list --at today

# 查看本周事件
timeline-cli event list --at 2026-06-16..2026-06-22 --json

# 显示 ID
timeline-cli event list --at today --show-id
```

---

## Note 操作

### 添加 Note

```bash
timeline-cli note add DATE TEXT
```

参数：
- `DATE` — 必填，日期（YYYY-MM-DD 格式）
- `TEXT` — 必填，笔记内容

每个日期只有一个 Note。已存在时会报错。

示例：
```bash
timeline-cli note add 2026-06-22 "今天很高效，完成了三个任务"
```

### 查看 Note

```bash
timeline-cli note show DATE
```

参数：
- `DATE` — 必填，日期（YYYY-MM-DD 格式）

示例：
```bash
timeline-cli note show 2026-06-22
```

### 编辑 Note

```bash
timeline-cli note edit DATE TEXT
```

参数：
- `DATE` — 必填，日期（YYYY-MM-DD 格式）
- `TEXT` — 必填，新的笔记内容（完全覆盖）

示例：
```bash
timeline-cli note edit 2026-06-22 "更新后的笔记内容"
```

---

## Diary 命令

显示一天的完整视图（events + todos + notes），以 markdown 格式输出。

```bash
timeline-cli diary [DATE] [--show-id]
```

参数：
- `DATE` — 可选，日期（默认 `today`，支持 `YYYY-MM-DD` 或 `today/yesterday/tomorrow`）
- `--show-id` — 可选，在输出中显示各条目的 ID

示例：
```bash
# 查看今日
timeline-cli diary

# 查看昨日
timeline-cli diary yesterday

# 查看特定日期（显示 ID）
timeline-cli diary 2026-06-22 --show-id
```

---

## Doctor 命令

校验数据完整性。

```bash
timeline-cli doctor [--fix]
```

参数：
- `--fix` — 可选，自动修复可修复的问题（目前仅修复排序问题）

校验项包括：JSON 有效性、schema_version、日期/时间格式、状态值、必填字段、排序、undated 约束、Note 唯一性、ID 唯一性。

示例：
```bash
# 校验数据
timeline-cli doctor

# 校验并自动修复
timeline-cli doctor --fix
```

---

## 其他命令

### init

初始化存储文件。

```bash
timeline-cli init
```

初始化 `.timeline/` 目录及 `data.jsonl` 文件。已存在时会报错。

### list

列出所有有记录的日期。

```bash
timeline-cli list
```

输出 markdown 格式，显示每个日期及该日期的条目数量。