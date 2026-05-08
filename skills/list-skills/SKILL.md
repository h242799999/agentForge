---
name: list-skills
description: Use when the user asks what skills or agents are available, "what can I use", "list my skills", "show agents", "有哪些skill", "有哪些agent", "能用什么工具". Displays all personal skills, agents, and installed plugins with descriptions and invocation commands.
tools: Bash
disable-model-invocation: false
---

# list-skills：查看所有可用 Skill 和 SubAgent

## 执行（一条命令完成所有输出）

运行以下脚本，收集并格式化输出：

```bash
extract() {
  local file="$1" field="$2"
  awk -v f="$field" '/^---/{c++; next} c==1 && $0 ~ "^"f":"{sub("^"f":[[:space:]]*",""); print; exit}' "$file" | cut -c1-60
}

echo "## 个人 Skills"
echo "| 名称 | 调用方式 | 简介 |"
echo "|---|---|---|"
for f in ~/.claude/skills/*/SKILL.md; do
  [ -f "$f" ] || continue
  name=$(extract "$f" "name")
  desc=$(extract "$f" "description")
  [ -n "$name" ] && echo "| \`$name\` | \`/$name\` | $desc |"
done

echo ""
echo "## 个人 SubAgents"
echo "| 名称 | 调用方式 | 简介 |"
echo "|---|---|---|"
for f in ~/.claude/agents/*/AGENT.md; do
  [ -f "$f" ] || continue
  name=$(extract "$f" "name")
  desc=$(extract "$f" "description")
  [ -n "$name" ] && echo "| \`$name\` | \`@$name\` | $desc |"
done

if ls .claude/skills/*/SKILL.md 2>/dev/null | grep -q .; then
  echo ""
  echo "## 项目 Skills（当前项目）"
  echo "| 名称 | 调用方式 | 简介 |"
  echo "|---|---|---|"
  for f in .claude/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    name=$(extract "$f" "name")
    desc=$(extract "$f" "description")
    [ -n "$name" ] && echo "| \`$name\` | \`/$name\` | $desc |"
  done
fi

if ls .claude/agents/*/AGENT.md 2>/dev/null | grep -q .; then
  echo ""
  echo "## 项目 SubAgents（当前项目）"
  echo "| 名称 | 调用方式 | 简介 |"
  echo "|---|---|---|"
  for f in .claude/agents/*/AGENT.md; do
    [ -f "$f" ] || continue
    name=$(extract "$f" "name")
    desc=$(extract "$f" "description")
    [ -n "$name" ] && echo "| \`$name\` | \`@$name\` | $desc |"
  done
fi

echo ""
echo "## 已安装插件"
echo "| 插件名 | Skills | Agents |"
echo "|---|---|---|"
for plugin_dir in ~/.claude/plugins/cache/*/*/; do
  [ -d "$plugin_dir" ] || continue
  plugin_name="$(basename "$plugin_dir")"
  # 取最新版本
  latest=$(ls -d "$plugin_dir"*/ 2>/dev/null | sort -V | tail -1)
  [ -d "$latest" ] || continue
  skill_count=$(find "$latest" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
  agent_count=$(find "$latest" -name "AGENT.md" 2>/dev/null | wc -l | tr -d ' ')
  [ "$skill_count" -gt 0 ] || [ "$agent_count" -gt 0 ] || continue
  version=$(basename "$latest")
  echo "| \`$plugin_name\` ($version) | $skill_count | $agent_count |"
done | sort -u
```

## 输出后的说明

- **Skills** 用 `/名称` 调用（如 `/commit-reviewer`）
- **SubAgents** 用 `@名称` 调用（如 `@commit-reviewer`），或在 `Agent` 工具中指定
- **插件 Skills** 用 `/插件名:skill名` 调用（如 `/superpowers:brainstorming`）
- 插件 Skills 的完整列表在每次会话开始的 system-reminder 中已列出
