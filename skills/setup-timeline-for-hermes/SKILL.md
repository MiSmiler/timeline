---
name: setup-timeline-for-hermes
description: "Deploy timeline skill to Hermes Agent: inject AGENTS.md into user project. 一键部署 timeline 的 Hermes 环境。"
tags: []
related_skills: ["timeline"]
---

# setup-timeline-for-hermes 技能

部署 timeline skill 的 Hermes 运行环境：注入 AGENTS.md、创建数据目录。

**触发条件**：用户说「部署 timeline」「setup timeline」等。

---

## 部署步骤

运行注入脚本，将 timeline 使用规则写入用户项目的 AGENTS.md，同时创建 `timelines/` 数据目录：

```bash
python3 skills/setup-timeline-for-hermes/scripts/setup_agents.py [target_dir]
```

- `target_dir` 可选，默认为当前目录
- 脚本会自动：
  - 创建 `timelines/` 目录
  - 将 `templates/AGENTS_TEMPLATE.md` 的内容注入到 `target_dir/AGENTS.md`
  - 用 `<!-- timeline-setup-start -->` / `<!-- timeline-setup-end -->` 包裹，支持幂等重跑

---

## Re-setup（重新部署）

### 1. 注入模板 + 清理 AGENTS.md

```bash
python3 skills/setup-timeline-for-hermes/scripts/setup_agents.py .
```

`setup_agents.py` 只处理 marker 区域（幂等替换），但旧的 AGENTS.md 可能有 marker 外的过时内容。重跑后检查：

1. 运行 `setup_agents.py`（自动追加/替换 marker 区域）
2. 检查 marker 外是否有与模板冲突的旧内容
3. 如有，手动清理或重写 AGENTS.md（保留项目头 + marker 区域即可）

### 2. 验证清单

```bash
# 数据目录存在
ls timelines/

# AGENTS.md 有 marker 且内容正确
grep -c "timeline-setup-start" AGENTS.md
```

---