# timeline

Timeline 工具的开发仓库。Timeline 是一个基于 markdown 文件的待办/事件管理工具，以 Hermes Agent skill 形式交付。

## 包含 Skills

| Skill | 说明 | 触发词 |
|-------|------|--------|
| timeline | 运行时 skill，管理待办事项和事件 | 「提醒」「待办」「做完了」「今天有什么事」 |
| setup-timeline | 部署 skill，配置 Hermes 环境并注入 AGENTS.md | 「部署 timeline」「setup timeline」 |

## 用户使用流程

1. **首次使用**：加载 `setup-timeline` skill，完成 Hermes 环境部署（wrapper 脚本 + AGENTS.md 注入 + 数据目录）
2. **日常使用**：直接通过自然语言触发 `timeline` skill 管理待办和事件

## 开发

详见 [AGENTS.md](AGENTS.md)。
