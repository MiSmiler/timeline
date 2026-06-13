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

### 3. 注入 AGENTS.md + 创建数据目录

运行注入脚本，将 timeline 使用规则写入用户项目的 AGENTS.md，同时创建 `timelines/` 数据目录：

```bash
python3 "$(dirname "$0")/setup_agents.py" [target_dir]
```

- `target_dir` 可选，默认为当前目录
- 脚本会自动：
  - 创建 `timelines/` 目录
  - 将 `templates/AGENTS_TEMPLATE.md` 的内容注入到 `target_dir/AGENTS.md`
  - 用 `<!-- timeline-setup-start -->` / `<!-- timeline-setup-end -->` 包裹，支持幂等重跑

**路径说明**：`$(dirname "$0")` 解析为 skill 的 `scripts/` 目录，模板从 `templates/AGENTS_TEMPLATE.md`（同级）读取。

### 4. 验证

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
- **脚本**：`todo_by_time.sh`（不传参数，自动用当前时间匹配）
- **模式**：`no_agent`（脚本直接输出，无 LLM 开销）
- **推送**：所有已连接渠道（`deliver: "all"`）
- **行为**：有到期待办则推送，无则静默

Cron job 创建示例：

```json
{
  "action": "create",
  "name": "timeline-20260612-1500",
  "schedule": "2026-06-12T15:00:00",
  "script": "todo_by_time.sh",
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

## Re-setup（重新部署）

在已有项目上重跑 setup 时，执行以下步骤：

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
python3 /path/to/skills/setup-timeline/scripts/setup_agents.py .
```

`setup_agents.py` 只处理 marker 区域（幂等替换），但旧的 AGENTS.md 可能有 marker 外的过时内容。重跑后检查：

1. 运行 `setup_agents.py`（自动追加/替换 marker 区域）
2. 检查 marker 外是否有与模板冲突的旧内容
3. 如有，手动清理或重写 AGENTS.md（保留项目头 + marker 区域即可）

典型需要清理的旧内容：
- 引用 `timeline/` 而非 `timelines/`
- 引用 `skills/timeline/SKILL.md`（硬编码路径）而非 `timeline` skill（按需加载）
- 包含脚本路径细节（应由 wrapper 处理，不在 AGENTS.md 中）

### 3. 验证清单

按顺序检查，全部通过才算部署完成：

```bash
# 1. Wrapper 脚本存在且内容正确
ls -la "$HERMES_HOME/scripts/"  # 应有 4 个 .sh
cat "$HERMES_HOME/scripts/todo_overdue.sh"  # cd 路径和 python3 路径是否正确

# 2. 数据目录存在
ls timelines/  # 应有 .md 文件

# 3. AGENTS.md 有 marker 且内容正确
grep -c "timeline-setup-start" AGENTS.md  # 应为 1
grep "timelines/" AGENTS.md  # 应引用 timelines/ 而非 timeline/

# 4. 脚本可运行
bash "$HERMES_HOME/scripts/todo_overdue.sh"
bash "$HERMES_HOME/scripts/todo_list.sh"
bash "$HERMES_HOME/scripts/validate.sh"

# 5. Cron job 配置正确（如有）
# timeline-hourly 应存在，script=todo_overdue.sh，no_agent=true
```

### 4. Profile `$HOME` 陷阱

命名 profile 的 `$HOME` 被重定向到 `~/.hermes/profiles/<name>/home/`，会覆盖真实 `~/.gitconfig` 等配置文件。如果发现 git commit author 不对：

```bash
# 检查 profile 的 gitconfig 是否覆盖了真实的
git config --list --show-origin | grep "user\."

# 修复：把真实的 .gitconfig 同步到 profile
cp ~/.gitconfig ~/.hermes/profiles/<profile>/home/.gitconfig
```

注意 `$HOME`（shell/git 读的）和 `HERMES_HOME`（Hermes 数据目录）是两个不同的路径。

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
