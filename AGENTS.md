# Timeline 工具开发

Timeline 是一个基于 markdown 文件的待办/事件管理工具，以 Hermes Agent skill 形式交付。

## 测试

在本地验证脚本行为：

```bash
# 验证数据一致性
python3 skills/timeline/scripts/validate.py

# 列出所有未完成待办
python3 skills/timeline/scripts/todo_list.py

# 按时间提取（不传参数用当前时间）
python3 skills/timeline/scripts/todo_by_time.py

# 提取过期 + 无时间待办
python3 skills/timeline/scripts/todo_overdue.py
```

## 用户使用

本项目的 skills 目录通过 Hermes 的 `external_dirs` 注册到用户 profile。用户通过自然语言触发 `timeline` skill 使用。

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues. Uses `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `CONTEXT.md` and `docs/adr/` at repo root. See `docs/agents/domain.md`.
