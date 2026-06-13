# Timeline 工具开发

Timeline 是一个基于 markdown 文件的待办/事件管理工具，以 Hermes Agent skill 形式交付。

## 开发约定

- **修改 timeline SKILL.md** → 检查是否需要同步更新 `setup-timeline/templates/AGENTS_TEMPLATE.md`
- **修改/新增脚本** → 检查是否需要更新 `setup-timeline/SKILL.md` 的 wrapper 列表
- **修改 cron 规则** → 同步更新 `references/cron-design.md`

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

测试 AGENTS.md 注入：

```bash
# 在临时目录测试
mkdir -p /tmp/test-timeline
python3 skills/setup-timeline/scripts/setup_agents.py /tmp/test-timeline
cat /tmp/test-timeline/AGENTS.md

# 重复运行验证幂等性
python3 skills/setup-timeline/scripts/setup_agents.py /tmp/test-timeline
cat /tmp/test-timeline/AGENTS.md
```

## 用户使用

本项目的 skills 目录通过 Hermes 的 `external_dirs` 注册到用户 profile。用户使用流程：

1. 首次使用：加载 `setup-timeline` skill → 部署 wrapper 脚本 + 注入 AGENTS.md + 创建 `timelines/` 目录
2. 日常使用：直接通过自然语言触发 `timeline` skill

## 发布

用户需要将 `skills/` 目录添加到其 Hermes profile 的 `external_dirs` 配置中，以便 Hermes 自动识别 timeline 和 setup-timeline skill。

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues. Uses `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `CONTEXT.md` and `docs/adr/` at repo root. See `docs/agents/domain.md`.
