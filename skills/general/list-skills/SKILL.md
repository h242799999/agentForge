---
name: list-skills
description: Use when the user asks what skills or agents are available, "what can I use", "list my skills", "show agents", "有哪些skill", "有哪些agent", "能用什么工具". Displays all personal skills, agents, and installed plugins with descriptions and invocation commands.
tools: Bash
disable-model-invocation: false
---

# list-skills：查看所有可用 Skill 和 SubAgent

## 零 token 调用方式（推荐）

在 Claude Code 输入框直接运行，**不消耗任何 token**：

```
! bash ~/.claude/scripts/list-skills.sh
```

## 通过 Skill 调用（消耗少量 token）

```bash
bash ~/.claude/scripts/list-skills.sh
```
