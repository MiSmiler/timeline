---
name: setup-timeline-for-hermes
description: "Deploy timeline skill to Hermes Agent: inject AGENTS.md into user project, configure cron jobs. 一键部署 timeline 的 Hermes 环境。"
tags: []
related_skills: ["timeline"]
---

# setup-timeline-for-hermes 技能

部署 timeline skill 的 Hermes 运行环境。包含注入 AGENTS.md、配置 cron job。

**触发条件**：用户说「部署 timeline」「设置 timeline cron」「setup timeline」等。

---

## 部署步骤

### 1. 注入 AGENTS.md + 创建数据目录

运行注入脚本，将 timeline 使用规则写入用户项目的 AGENTS.md，同时创建 `timelines/` 数据目录：

```bash
python3 skills/setup-timeline-for-hermes/scripts/setup_agents.py [target_dir]
```

- `target_dir` 可选，默认为当前目录
- 脚本会自动：
  - 创建 `timelines/` 目录
  - 将 `templates/AGENTS_TEMPLATE.md` 的内容注入到 `target_dir/AGENTS.md`
  - 用 `<!-- timeline-setup-start -->` / `<!-- timeline-setup-end -->` 包裹，支持幂等重跑

### 2. 配置 Cron Job（可选）

根据 AGENTS.md 中的 cron 配置，使用 Hermes cronjob 工具创建定时任务。

---

## Cron Job 配置

根据 ADR-0001，cron 直接触发 timeline skill（接受 LLM 成本），不再使用 wrapper 脚本。

### 定时提醒（按 todo 时间）

- **触发时机**：创建或修改今天有时间的待办时
- **命名格式**：`timeline-{YYYYMMDD}-{HHMM}`（如 `timeline-20260612-1500`）
- **触发方式**：调用 timeline skill，响应"有什么到期的待办"类提示词
- **推送**：所有已连接渠道（`deliver: "all"`）

### 每小时扫描

- **触发频率**：每小时一次（避开整点）
- **命名**：`timeline-hourly`（固定）
- **触发方式**：调用 timeline skill，响应"过期的待办有什么"类提示词
- **推送**：所有已连接渠道

---

## Re-setup（重新部署）

### 1. 数据目录迁移

如果项目有旧的 `timeline/` 目录，需迁移到 `timelines/`：

```bash
cd /path/to/project
mkdir -p timelines
cp -r timeline/* timelines/
rm -rf timeline
```

### 2. 注入模板 + 清理 AGENTS.md

```bash
python3 skills/setup-timeline-for-hermes/scripts/setup_agents.py .
```

`setup_agents.py` 只处理 marker 区域（幂等替换），但旧的 AGENTS.md 可能有 marker 外的过时内容。重跑后检查：

1. 运行 `setup_agents.py`（自动追加/替换 marker 区域）
2. 检查 marker 外是否有与模板冲突的旧内容
3. 如有，手动清理或重写 AGENTS.md（保留项目头 + marker 区域即可）

### 3. 验证清单

```bash
# 1. 数据目录存在
ls timelines/

# 2. AGENTS.md 有 marker 且内容正确
grep -c "timeline-setup-start" AGENTS.md

# 3. Cron job 配置正确（如有）
# timeline-hourly 应存在，触发 timeline skill
```

---

## 设计决策

详见 `references/cron-design.md`。