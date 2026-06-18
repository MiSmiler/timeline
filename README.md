# Timeline CLI

基于 jsonline 存储的待办/事件/笔记管理工具。

## 安装

```bash
# 推荐：全局安装（隔离环境）
uv tool install .

# 或开发模式安装
uv sync
uv pip install -e .
```

## 使用

```bash
timeline-cli --help
timeline-cli todo add 2026-06-17 "完成报告"
timeline-cli todo list 2026-06-17
```

## 开发

```bash
# 安装依赖
uv sync

# 运行 CLI
uv run timeline-cli --help

# 格式化
uv run ruff format

# 检查
uv run ruff check

# 测试
uv run pytest
```

详细说明见 [AGENTS.md](AGENTS.md)。

## Roadmap

- todo list output有问题，markdown格式，把complete打在方括号里了。不过--json输出没问题，所以ai能用。
- 重新设计一下todo list --json的输出，应该输出jsonline
- 更新timeline skill的实现