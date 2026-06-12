# Timeline 部署指南（Hermes 专用）

> 以下操作仅在使用 Hermes Agent 的 cronjob 功能时需要。纯脚本用法无需此步骤。

## 背景

Hermes cronjob 工具的 script 字段只接受相对文件名，会自动解析到 `$HERMES_HOME/scripts/` 目录。

- `HERMES_HOME` 是 Hermes 环境变量，指向当前 profile 根目录
- default profile：`HERMES_HOME` = `~/.hermes` → 脚本放在 `~/.hermes/scripts/`
- 命名 profile（如 `oicat-v2`）：`HERMES_HOME` = `~/.hermes/profiles/<profile>` → 脚本放在 `~/.hermes/profiles/<profile>/scripts/`

## 创建 Symlink

在 Hermes 终端中执行：

    mkdir -p "$HERMES_HOME/scripts"

    # 修改为你的项目实际路径
    SOURCE_DIR="/path/to/your/project/skills/timeline/scripts"

    for script in todo_by_time.py todo_list.py todo_overdue.py validate.py; do
      ln -sf "$SOURCE_DIR/$script" "$HERMES_HOME/scripts/$script"
    done

验证：

    ls -la "$HERMES_HOME/scripts/"  # 确认 symlink 存在且未断链

## 创建 Cron Job 时

script 字段只写文件名（不含路径）：

    script: "todo_overdue.py"
    script: "todo_by_time.py 2026-06-12 15:00"

## 维护规则

| 操作 | 后果 |
|------|------|
| 修改脚本内容 | symlink 正常，内容同步 |
| 重命名/删除脚本 | 断链 → cron 报错（非零退出 → 错误告警） |
| 新增脚本需 cron 调用 | 需同步添加 symlink |
| 切换 profile | 需在新 profile 下重新创建 symlink |

建议：脚本是稳定工具，极少变动。如有变动，记得同步 `$HERMES_HOME/scripts/` 下的 symlink。