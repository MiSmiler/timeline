# Cron Job 设计决策记录

本文档记录 timeline cron 系统的设计决策和 rationale，供后续维护参考。

## 决策背景

用户希望 todo 能通过 cron job 按时提醒，同时有一个每小时扫描机制处理过期和无时间的待办。

## 决策 1：动态创建 cron vs 固定轮询

**选择**：动态创建 cron job（每个时间点一个）

**被否决的方案**：
- 每分钟轮询：太频繁，浪费资源
- 每5分钟轮询：延迟最多5分钟，不够精准
- 每天早上批量推送：用户想要准时提醒

**Rationale**：按需创建，精准触发，无 LLM 开销（no_agent 模式）。

## 决策 2：cron 命名格式

**选择**：`timeline-{YYYYMMDD}-{HHMM}`

**被否决的方案**：`timeline-{HHMM}`（会跨天冲突）

**Rationale**：用户可能今天和明天都有 15:00 的待办，需要区分。

## 决策 3：同一时间多 todo 的处理

**选择**：合并为一个 cron job，脚本输出所有匹配项

**被否决的方案**：每条 todo 一个 cron job

**Rationale**：减少 cron 数量，一次推送完整信息，生命周期管理更简单。

## 决策 4：cron 范围

**选择**：只管理今天的待办，跨天的由 daily review 负责

**被否决的方案**：创建时就建 cron（不管哪天）

**Rationale**：简化生命周期。非今天的 todo 改动频率低，由 daily review 统一处理更可靠。

## 决策 5：完成/取消待办的 cron 清理

**选择**：检查同时间是否还有其他待办，无则删 cron

**Rationale**：保持 cron 列表干净，避免空跑。

## 决策 6：每小时扫描的内容

**选择**：过期（日期已过 OR 时间已过）+ 无时间待办

**被否决的方案**：只扫描过期待办

**Rationale**：无时间待办属于"待定项"，用户应主动管理，每小时提醒有助于推动用户决策。

## 脚本 API

### todo_by_time.py
- 输入：`YYYY-MM-DD HH:MM`
- 输出：匹配的未完成 todo（有则输出，无则静默）
- 用途：per-time cron job 的执行脚本

### todo_overdue.py
- 输入：`[YYYY-MM-DD HH:MM]`（可选，默认当前时间）
- 输出：过期待办 + 无时间待办（有则输出，无则静默）
- 用途：hourly sweep cron job 的执行脚本

### todo_list.py
- 输入：无
- 输出：所有未完成 todo
- 用途：查看/调试用

### validate.py
- 输入：无
- 输出：验证结果
- 用途：数据一致性检查

## 未来扩展

- **daily review skill**：每天早上为当天待办创建 cron job（待实现）
- **跨天 todo 的 cron**：目前不支持，依赖 daily review

## 决策 7：每小时扫描的时间和范围

**选择**：`58 9-23 * * *`（每天 09:58~23:58）

**Rationale**：
- 整点前 2 分钟触发，避免与用户自己设置的整点 per-time cron 撞车
- 9-23 范围推送，深夜不打扰
- 脚本不传参数，用 `datetime.now()` 取当前时间（:58），行为合理

**被否决的方案**：
- 整点（XX:00）：与 per-time cron 冲突
- 整点后（XX:02）：作为迟到提醒，但用户选择提前
- 每小时全时段：深夜打扰

## 决策 8：cronjob 脚本路径限制

**问题**：cronjob 工具不允许绝对路径，报错 `Script path must be relative to ~/.hermes/scripts/`

**解决方案**：symlink 到 `~/.hermes/scripts/`
```bash
mkdir -p ~/.hermes/scripts
ln -sf /home/hui/notenote/daynote/skills/timeline/scripts/todo_overdue.py ~/.hermes/scripts/todo_overdue.py
ln -sf /home/hui/notenote/daynote/skills/timeline/scripts/todo_by_time.py ~/.hermes/scripts/todo_by_time.py
```

**已知问题**：现有 per-time cron job（如 `timeline-20260612-1600`）使用的 `scripts/todo_by_time.py` 路径可能也有同样问题，需排查修复。
