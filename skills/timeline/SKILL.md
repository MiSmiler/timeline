---
name: timeline
description: "timeline-cli 操作指南。定义 Todo/Event/Note 的 CRUD 操作语义、日期处理、定位规则和错误处理策略。"
tags: []
related_skills: []
---

# Timeline CLI 操作指南

timeline-cli 是一个基于 JSONL 存储的待办/事件/笔记管理工具。Agent 应通过 CLI 命令操作数据，而非直接操作文件。

数据格式参考：[reference/data-format.md](reference/data-format.md)

---

## 日期处理

CLI 只接受 `YYYY-MM-DD` 格式的日期（如 `2026-06-17`）。

Agent 负责将自然语言日期转换为标准格式：
- "今天" → 当前日期
- "明天" → 当前日期 + 1
- "昨天" → 当前日期 - 1
- "下周一" → 计算具体日期

---

## 操作语义

以下操作均通过 `timeline-cli` 命令执行。推荐使用 `--json` 参数获取结构化输出。

### Todo 操作

#### 创建 Todo

```bash
timeline-cli todo add <date> <text> [--time TIME] [--detail DETAIL]
```

- `date`: 必填，YYYY-MM-DD 格式
- `text`: 必填，待办描述
- `--time`: 可选，HH:MM 格式
- `--detail`: 可选，详情文本

示例：
```bash
# 创建无时间待办
timeline-cli todo add 2026-06-17 "写测试"

# 创建有时间待办
timeline-cli todo add 2026-06-17 "开会" --time 14:00

# 创建带详情的待办
timeline-cli todo add 2026-06-17 "整理桌面" --detail "扔掉过期零食"
```

#### 完成 Todo

```bash
timeline-cli todo complete <date> [--time TIME] <text_prefix>
```

- 定位：`date + text` 全文匹配，歧义时需加 `--time`
- 推荐：完成后可选创建 Event 记录完成时间

示例：
```bash
timeline-cli todo complete 2026-06-17 "写测试"
```

#### 放弃 Todo

```bash
timeline-cli todo abandon <date> [--time TIME] <text_prefix>
```

- 放弃保留记录，状态变为 `abandoned`
- 与删除的区别：放弃保留条目，删除则移除

示例：
```bash
timeline-cli todo abandon 2026-06-17 "过期的任务"
```

#### 编辑 Todo

```bash
timeline-cli todo edit <date> [--time TIME] <text_prefix> \
  [--new-text TEXT] [--new-time TIME] \
  [--append-detail TEXT] [--set-detail TEXT]
```

- `--new-text`: 更新描述
- `--new-time`: 更新时间
- `--append-detail`: 追加详情
- `--set-detail`: 覆盖详情

示例：
```bash
# 更新描述
timeline-cli todo edit 2026-06-17 "写测试" --new-text "写单元测试"

# 追加详情
timeline-cli todo edit 2026-06-17 "写测试" --append-detail "需要 mock"

# 更新时间
timeline-cli todo edit 2026-06-17 "开会" --time 14:00 --new-time 15:00
```

#### 移动 Todo

```bash
timeline-cli todo move <from_date> <to_date> [--time TIME] <text_prefix>
```

- 将待办从一个日期移动到另一个日期

示例：
```bash
timeline-cli todo move 2026-06-17 2026-06-18 "写测试"
```

#### 删除 Todo

```bash
timeline-cli todo delete <date> [--time TIME] <text_prefix> [--yes]
```

- **删除前确认**：Agent 先与用户确认，确认后加 `--yes` 参数
- 删除不留痕迹，与放弃不同

示例：
```bash
# Agent 确认后执行
timeline-cli todo delete 2026-06-17 "废弃的任务" --yes
```

#### 补充 Todo 详情

```bash
timeline-cli todo edit <date> [--time TIME] <text_prefix> --append-detail TEXT
```

- 可多次追加，不会覆盖已有详情

---

### Event 操作

#### 创建 Event

```bash
timeline-cli event add <date> --time TIME <text> [--detail DETAIL]
```

- `--time`: **必填**，HH:MM 格式
- 用户未指定时间时，默认使用当前时间

示例：
```bash
timeline-cli event add 2026-06-17 --time 09:00 "团队会议"
timeline-cli event add 2026-06-17 --time 14:30 "完成报告" --detail "提交到系统"
```

#### 编辑 Event

```bash
timeline-cli event edit <date> <time> <text_prefix> \
  [--new-text TEXT] [--new-time TIME] \
  [--append-detail TEXT] [--set-detail TEXT]
```

- 定位：`date + time + text` 匹配

示例：
```bash
timeline-cli event edit 2026-06-17 09:00 "团队会议" --new-time 10:00
```

#### 删除 Event

```bash
timeline-cli event delete <date> <time> <text_prefix> [--yes]
```

- **删除前确认**：Agent 先与用户确认，确认后加 `--yes` 参数

示例：
```bash
timeline-cli event delete 2026-06-17 09:00 "取消的会议" --yes
```

#### 补充 Event 详情

```bash
timeline-cli event edit <date> <time> <text_prefix> --append-detail TEXT
```

---

### Note 操作

#### 添加 Note

```bash
timeline-cli note add <date> <text>
```

- 每个日期只有一个 Note
- 如果已存在 Note，会报错

示例：
```bash
timeline-cli note add 2026-06-17 "今天很高效，完成了三个任务"
```

#### 查看 Note

```bash
timeline-cli note show <date>
```

示例：
```bash
timeline-cli note show 2026-06-17
```

#### 编辑 Note

```bash
timeline-cli note edit <date> <text>
```

- 完全覆盖原有 Note

示例：
```bash
timeline-cli note edit 2026-06-17 "更新后的笔记内容"
```

---

### 查询与导出

#### 列出 Todo

```bash
timeline-cli todo list [--date DATE] [--time TIME] [--status STATUS] [--overdue] [--undated] [--json] [text_prefix]
```

- `--date`: 按日期筛选
- `--time`: 按时间筛选
- `--status`: 按状态筛选（`pending`/`completed`/`abandoned`）
- `--overdue`: 显示过期待办
- `--undated`: 显示无日期待办
- `--json`: JSON 格式输出
- `text_prefix`: 文本前缀匹配

示例：
```bash
# 列出所有未完成待办
timeline-cli todo list --status pending --json

# 列出特定日期的待办
timeline-cli todo list --date 2026-06-17 --json
```

#### 列出 Event

```bash
timeline-cli event list <date> [--json]
```

示例：
```bash
timeline-cli event list 2026-06-17 --json
```

#### 列出日期

```bash
timeline-cli list [--json]
```

- 列出所有有记录的日期

#### 导出为 Markdown

```bash
timeline-cli export <date> --output-dir DIR
timeline-cli export-all --output-dir DIR
```

- 导出单个日期或所有日期为 Markdown 文件

---

## 错误处理

### 常见错误类型

#### ambiguous_match（匹配歧义）

**原因**：多个条目匹配 `date + text` 条件

**处理**：使用 `--time` 参数精确匹配

示例：
```bash
# 歧义：两个待办都叫"开会"
timeline-cli todo complete 2026-06-17 "开会"
# 错误：ambiguous_match，显示候选条目

# 解决：加 --time
timeline-cli todo complete 2026-06-17 "开会" --time 14:00 --yes
```

#### not_found（未找到）

**原因**：没有匹配的条目

**处理**：检查日期、时间、文本是否正确

#### validation_error（校验错误）

**原因**：数据格式不符合约束（如 0000-00-00 中的 Event）

**处理**：检查数据约束，使用 `timeline-cli doctor` 校验

### 错误响应格式

CLI 返回结构化错误信息（JSON 格式）：

```json
{
  "error": "ambiguous_match",
  "message": "Multiple todos match",
  "candidates": [
    {"time": "09:00", "text": "开会"},
    {"time": "14:00", "text": "开会"}
  ]
}
```

Agent 应根据 `error` 字段决定重试策略。