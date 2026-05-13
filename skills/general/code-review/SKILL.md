---
name: code-review
description: 全局代码审查总入口。--commit 选择内容来源（提交 diff），--code/--business/--ui/--all 选择审查维度，两者可自由组合。通过 --project 指定项目或自动检测。当用户说"review代码"、"检查代码"、"审查提交"等未明确项目时触发。
tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# Code Review — 全局审查入口

> 统一调度器，自动路由到对应项目的审查 skill。
> `--commit` 决定**看什么**（文件 vs 提交 diff），维度 flag 决定**怎么审**，两者正交组合。

---

## 调用语法

```
/code-review [--project xq|shimano] [--commit [id]] [--code|--business|--ui|--all] [<target>]
```

### 参数说明

| 参数 | 作用 | 默认值 |
|------|------|--------|
| `--project` | 目标项目 | 自动检测 |
| `--commit [id]` | 来源 = 提交 diff，id 省略时为 HEAD | — |
| `<target>` | 目标文件或目录（文件模式时必填） | 当前目录 |
| `--code` | 审查维度：代码规范 + 逻辑 | — |
| `--business` | 审查维度：业务逻辑 | — |
| `--ui` | 审查维度：KMP/Compose UI | — |
| `--all` | 审查维度：code + business + ui | — |
| 无维度 flag | 默认：code + business | — |

---

## 调用示例

```bash
# 文件审查（自动检测项目）
/code-review src/wifi/                           # code + business（默认）
/code-review src/wifi/ --code                    # 仅代码规范
/code-review src/auth/ --business                # 仅业务逻辑
/code-review src/screens/ --ui                   # 仅 UI
/code-review src/ --all                          # 全量

# 提交审查（自动检测项目）
/code-review --commit                            # HEAD，code + business
/code-review --commit abc123                     # 指定 commit，code + business
/code-review --commit --code                     # HEAD，仅代码规范
/code-review --commit abc123 --business          # 指定 commit，仅业务
/code-review --commit --ui                       # HEAD，仅 UI
/code-review --commit abc123 --all               # 指定 commit，全量

# 指定项目
/code-review --project xq --commit --business    # XQ 提交业务审查
/code-review --project shimano src/ --ui         # Shimano 文件 UI 审查
```

---

## Step 1：确定目标项目

**若用户已指定 `--project`**：直接使用。

**若未指定**，按以下顺序自动检测：

```bash
# 检查 git remote
git remote get-url origin 2>/dev/null

# 检查目标路径或 diff 中的特征
```

| 检测特征 | 分发至 |
|---------|--------|
| XQ 特征：`xq/`、`BLE`、`WifiConnection`、`PtpIp`、`X010` | `xq` |
| Shimano 特征：`shimano/`、`ShimanoLoader`、`BLEDevice`、`MyBike` | `shimano` |
| 无法识别 | 提示：`无法自动识别项目，请指定 --project xq 或 --project shimano` |

---

## Step 2：路由到项目 skill

加载对应项目的 skill 文件并按其流程执行：

```
xq 项目：   Read ~/.claude/skills/xq-review/SKILL.md
shimano 项目：Read ~/.claude/skills/shimano-review/SKILL.md
```

将用户传入的所有参数（`--commit [id]`、维度 flag、`<target>`）原样传递给对应 skill。

---

## Step 3：输出报告

按对应 skill 的报告格式输出，在报告头部追加来源标注：

```
> 由 /code-review 调度 → {project}-review
```

---

## 快速参考

```
╔══════════════════════════════════════════════════════════════╗
║                  /code-review 组合速查                        ║
╠═══════════════════════════╦══════════════════════════════════╣
║ 场景                      ║ 命令                             ║
╠═══════════════════════════╬══════════════════════════════════╣
║ 审查最近提交（全）        ║ /code-review --commit            ║
║ 审查最近提交（仅代码）    ║ /code-review --commit --code     ║
║ 审查最近提交（仅业务）    ║ /code-review --commit --business ║
║ 审查最近提交（仅UI）      ║ /code-review --commit --ui       ║
║ 审查最近提交（全量）      ║ /code-review --commit --all      ║
╠═══════════════════════════╬══════════════════════════════════╣
║ 指定 commit 全量          ║ /code-review --commit abc123 --all ║
║ 指定 commit 仅业务        ║ /code-review --commit abc123 --business ║
╠═══════════════════════════╬══════════════════════════════════╣
║ 文件审查（默认）          ║ /code-review src/module/         ║
║ 文件仅代码规范            ║ /code-review src/ --code         ║
║ 文件仅业务逻辑            ║ /code-review src/ --business     ║
║ 文件全量                  ║ /code-review src/ --all          ║
╠═══════════════════════════╬══════════════════════════════════╣
║ 指定项目                  ║ /code-review --project xq ...    ║
╚═══════════════════════════╩══════════════════════════════════╝
```
