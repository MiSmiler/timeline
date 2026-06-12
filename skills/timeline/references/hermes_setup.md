# Timeline 部署指南（Hermes 专用）

> 以下操作仅在使用 Hermes Agent 的 cronjob 功能时需要。纯脚本用法无需此步骤。

## 背景

Hermes cronjob 工具的 script 字段只接受相对文件名，会自动解析到 `$HERMES_HOME/scripts/` 目录。

- `HERMES_HOME` 是 Hermes 环境变量，指向当前 profile 根目录
- default profile：`HERMES_HOME` = `~/.hermes` → 脚本放在 `~/.hermes/scripts/`
- 命名 profile（如 `oicat-v2`）：`HERMES_HOME` = `~/.hermes/profiles/<profile>` → 脚本放在 `~/.hermes/profiles/<profile>/scripts/`

## 创建 Wrapper 脚本

**不能用 symlink**：Hermes 安全检查会解析 symlink 真实路径，指向 `scripts/` 目录外部的会被拦截。

用 bash wrapper 代替 — cd 到项目目录再调用 Python 脚本：

    mkdir -p "$HERMES_HOME/scripts"

    # 修改为你的项目实际路径
    PROJECT_DIR="/path/to/your/project"
    SOURCE_DIR="$PROJECT_DIR/skills/timeline/scripts"

    for script in todo_by_time.py todo_list.py todo_overdue.py validate.py; do
      sh_name="${script%.py}.sh"
      cat > "$HERMES_HOME/scripts/$sh_name" << EOF
    #!/bin/bash
    cd "$PROJECT_DIR" && python3 "$SOURCE_DIR/$script" "\$@"
    EOF
      chmod +x "$HERMES_HOME/scripts/$sh_name"
    done

验证：

    ls -la "$HERMES_HOME/scripts/"
    bash "$HERMES_HOME/scripts/todo_overdue.sh"  # 应正常输出

## 创建 Cron Job 时

script 字段写 `.sh` 文件名（Hermes 对 `.sh`/`.bash` 用 bash 执行，其他扩展名用 Python）：

    script: "todo_overdue.sh"
    script: "todo_by_time.sh 2026-06-12 15:00"

## 维护规则

| 操作 | 后果 |
|------|------|
| 修改源脚本内容 | wrapper 透明，内容同步（wrapper 调用的是源文件） |
| 重命名/删除源脚本 | wrapper 路径失效 → cron 报错 |
| 新增脚本需 cron 调用 | 需同步添加新 wrapper |
| 切换 profile | 需在新 profile 下重新创建 wrapper |

建议：脚本是稳定工具，极少变动。如有变动，记得同步 `$HERMES_HOME/scripts/` 下的 wrapper。
