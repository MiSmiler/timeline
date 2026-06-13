# timeline

Timeline 工具的开发仓库。Timeline 是一个基于 markdown 文件的待办/事件管理工具，以 Hermes Agent skill 形式交付。

## 包含 Skills

| Skill | 说明 | 触发词 |
|-------|------|--------|
| timeline | 数据格式层 skill，定义 markdown 文件结构和完整性约束 | （用户习惯层定义在 AGENTS.md） |
| setup-timeline-for-hermes | 平台适配层 skill，配置 Hermes cron 并注入 AGENTS.md | 「部署 timeline」「setup timeline」 |

## 用户使用流程

1. **首次使用**：加载 `setup-timeline-for-hermes` skill，完成 Hermes 环境部署（AGENTS.md 注入 + 数据目录 + cron 配置）
2. **日常使用**：直接通过自然语言触发 `timeline` skill 管理待办和事件

## 开发

详见 [AGENTS.md](AGENTS.md)。
