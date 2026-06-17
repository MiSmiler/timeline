# Timeline 数据格式参考

本文档定义 schema v1 的数据格式，供 agent 查阅 CLI 输出格式时参考。

## 文件结构

### 文件位置与创建

- 文件名：`timelines.jsonl`
- 创建方式：运行 `timeline-cli init`
- 格式：JSONL（每行一个 JSON 对象）

### 文件结构

```
第 1 行：{"schema_version": 1}        # Header，定义 schema 版本
第 2 行及之后：{"date": "...", ...}   # 每行一个 DailyRecord
```

---

## 数据类型定义

### DailyRecord（每日记录）

```json
{
  "date": "YYYY-MM-DD",
  "events": [...],
  "todos": [...],
  "notes": "string" | null
}
```

### Event（事件）

```json
{
  "time": "HH:MM",
  "text": "string",
  "details": ["line1", "line2"]
}
```

- `time`: **必填**，格式 `HH:MM`（如 `09:30`）
- `text`: 事件描述
- `details`: 详情数组，空数组为 `[]`

### Todo（待办）

```json
{
  "time": "HH:MM" | null,
  "text": "string",
  "status": "pending" | "completed" | "abandoned",
  "details": ["line1", "line2"]
}
```

- `time`: 可选，格式 `HH:MM` 或 `null`
- `text`: 待办描述
- `status`: 状态值，仅允许 `pending`、`completed`、`abandoned`
- `details`: 详情数组，空数组为 `[]`

### Note（笔记）

单个字符串或 `null`：

```json
"自由格式的笔记文本"
```

```json
null
```

---

## 0000-00-00 特殊约束

`0000-00-00` 日期用于存储无日期待办，有以下约束：

1. **events**: 必须为空数组 `[]`
2. **notes**: 必须为 `null`
3. **todos 的 time**: 必须为 `null`

违反约束会导致数据校验失败（`timeline-cli doctor` 会报告错误）。

---

## JSON 示例

### Header 行

```json
{"schema_version": 1}
```

### 普通日期记录

```json
{
  "date": "2026-06-17",
  "events": [
    {"time": "09:00", "text": "团队会议", "details": ["讨论了路线图"]},
    {"time": "14:30", "text": "完成报告", "details": []}
  ],
  "todos": [
    {"time": "10:00", "text": "写测试", "status": "pending", "details": []},
    {"time": null, "text": "整理桌面", "status": "completed", "details": []}
  ],
  "notes": "今天很高效"
}
```

### 0000-00-00 记录

```json
{
  "date": "0000-00-00",
  "events": [],
  "todos": [
    {"time": null, "text": " someday task", "status": "pending", "details": []}
  ],
  "notes": null
}
```

---

## 排序规则

- **Events**: 按 `time` 升序排序
- **Todos**: 有时间的在前（按 time 升序），无时间的在后

排序由 CLI 自动处理，添加或编辑条目后会自动重排。

---

## 数据完整性

CLI 自动维护数据完整性：
- 日期格式校验（`YYYY-MM-DD` 或 `0000-00-00`）
- 时间格式校验（`HH:MM`）
- 状态值校验（仅允许三种状态）
- 无重复日期
- 0000-00-00 约束校验

高级用户可使用 `timeline-cli doctor` 进行数据校验和修复。