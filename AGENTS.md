# Timeline CLI 开发

Timeline CLI 是一个基于 jsonline 存储的待办/事件/笔记管理工具，以 Python CLI 形式交付。

## 工具链

本项目使用以下工具链：

- **包管理**: [uv](https://docs.astral.sh/uv/) - 快速的 Python 包管理器
- **格式化/检查**: [ruff](https://docs.astral.sh/ruff/) - 极速 Python linter 和 formatter

## 常用命令

```bash
# 安装依赖
uv sync

# 运行 CLI
uv run timeline-cli --help

# 格式化代码
uv run ruff format

# 代码检查
uv run ruff check

# 运行测试（测试通过 CLI 入口点，参见 issue #6）
uv run pytest
```

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues. Uses `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `CONTEXT.md` and `docs/adr/` at repo root. See `docs/agents/domain.md`.
