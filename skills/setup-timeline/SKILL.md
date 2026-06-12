---
name: setup-timeline
description: "Deploy timeline skill to Hermes Agent: create wrapper scripts in $HERMES_HOME/scripts/, configure cron jobs. 一键部署 timeline 的 Hermes 环境。"
tags: []
related_skills: ["timeline"]
---

# setup-timeline 技能

部署 timeline skill 的 Hermes 运行环境。包含创建 wrapper 脚本、配置 cron job。

**触发条件**：用户说「部署 timeline」「设置 timeline cron」「setup timeline」等。

---

## 背景

Hermes cronjob 工具的 `script` 字段只接受相对文件名，自动解析到 `$HERMES_HOME/scripts/` 目录。

- `HERMES_HOME` 是 Hermes 环境变量，指向当前 profile 根目录
- default profile：`HERMES_HOME` = `~/.hermes` → 脚本放在 `~/.hermes/scripts/`
- 命名 profile（如 `oicat-v2`）：`HERMES_HOME` = `~/.hermes/profiles/<profile>` → 脚本放在 `~/.hermes/profiles/<profile>/scripts/`

### 为什么不能用 symlink

Hermes 安全检查会解析 symlink 的真实路径，指向 `scripts/` 目录外部的会被拦截。用 bash wrapper 代替。

---

## 部署步骤

### 1. 确认环境

```bash
echo $HERMES_HOME
# 确认输出路径存在且是当前使用的 profile
```

确认 timeline 脚本所在目录（项目根目录下的 `skills/timeline/scripts/`）：

```bash
ls skills/timeline/scripts/*.py
# 应看到: todo_by_time.py  todo_list.py  todo_overdue.py  validate.py
```

### 2. 创建 wrapper 脚本

为每个 `.py` 脚本生成对应的 `.sh` wrapper 到 `$HERMES_HOME/scripts/`：

```bash
mkdir -p "$HERMES_HOME/scripts"

PROJECT_DIR="$(pwd)"
SOURCE_DIR="$PROJECT_DIR/skills/timeline/scripts"

for script in todo_by_time.py todo_list.py todo_overdue.py validate.py; do
  sh_name="${script%.py}.sh"
  cat > "$HERMES_HOME/scripts/$sh_name" << EOF
#!/bin/bash
cd "$PROJECT_DIR" && python3 "$SOURCE_DIR/$script" "\$@"
EOF
  chmod +x "$HERMES_HOME/scripts/$sh_name"
done
```

### 3. 验证

```bash
ls -la "$HERMES_HOME/scripts/"
# 应看到 todo_by_time.sh, todo_list.sh, todo_overdue.sh, validate.sh

bash "$HERMES_HOME/scripts/todo_overdue.sh"
# 应正常输出（有内容则显示，无内容则静默）
```

---

## Cron Job 配置

### 定时提醒（按 todo 时间）

- **触发时机**：创建或修改今天有时间的待办时
- **命名格式**：`timeline-{YYYYMMDD}-{HHMM}`（如 `timeline-20260612-1500`）
- **脚本**：`todo_by_time.sh YYYY-MM-DD HH:MM`
- **模式**：`no_agent`（脚本直接输出，无 LLM 开销）
- **推送**：所有已连接渠道（`deliver: "all"`）
- **行为**：有到期待办则推送，无则静默

Cron job 创建示例：

```json
{
  "action": "create",
  "name": "timeline-20260612-1500",
  "schedule": "2026-06-12T15:00:00",
  "script": "todo_by_time.sh 2026-06-12 15:00",
  "no_agent": true,
  "deliver": "all"
}
```

### 每小时扫描

- **触发频率**：`58 9-23 * * *`（09:58~23:58，避开整点 per-time cron）
- **命名**：`timeline-hourly`（固定）
- **脚本**：`todo_overdue.sh`（不传参数，用 `datetime.now()` 取当前时间）
- **模式**：`no_agent`
- **推送**：所有已连接渠道
- **内容**：过期未完成待办 + 无时间待办（有则推送，无则静默）

---

## 维护规则

| 操作 | 后果 | 处理 |
|------|------|------|
| 修改源脚本内容 | wrapper 透明，无需同步 | 无需操作 |
| 重命名/删除源脚本 | wrapper 路径失效 → cron 报错 | 同步更新或重建 wrapper |
| 新增脚本需 cron 调用 | 无对应 wrapper | 添加新 wrapper（同部署步骤） |
| 切换 profile | 新 profile 无 wrapper | 在新 profile 下重新执行部署步骤 |
| 修改项目目录位置 | wrapper 内路径失效 | 重新执行部署步骤 |

---

## 设计决策

详见 `references/cron-design.md`。
