#!/usr/bin/env bash
# list-skills.sh — 列出所有已部署的 Skills、SubAgents 和插件
# 零 token 消耗，直接在 shell 运行
# 用法：
#   bash ~/.claude/scripts/list-skills.sh
#   在 Claude Code 中：! ~/.claude/scripts/list-skills.sh

extract() {
  local file="$1" field="$2"
  awk -v f="$field" '/^---/{c++; next} c==1 && $0 ~ "^"f":"{sub("^"f":[[:space:]]*",""); print; exit}' "$file" | cut -c1-60
}

CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"

echo "## 个人 Skills"
echo "| 名称 | 调用方式 | 简介 |"
echo "|---|---|---|"
for f in "$CLAUDE_DIR/skills/"*/SKILL.md; do
  [ -f "$f" ] || continue
  name=$(extract "$f" "name")
  desc=$(extract "$f" "description")
  [ -n "$name" ] && echo "| \`$name\` | \`/$name\` | $desc |"
done

echo ""
echo "## 个人 SubAgents"
echo "| 名称 | 调用方式 | 简介 |"
echo "|---|---|---|"
found_agent=0
for f in "$CLAUDE_DIR/agents/"*/AGENT.md; do
  [ -f "$f" ] || continue
  name=$(extract "$f" "name")
  desc=$(extract "$f" "description")
  [ -n "$name" ] && echo "| \`$name\` | \`@$name\` | $desc |" && found_agent=1
done
[ "$found_agent" -eq 0 ] && echo "| (无) | — | — |"

echo ""
echo "## 已安装插件"
echo "| 插件名 | Skills | Agents |"
echo "|---|---|---|"
plugin_rows=""
for plugin_dir in "$CLAUDE_DIR/plugins/cache/"*/ ; do
  [ -d "$plugin_dir" ] || continue
  for vendor_plugin_dir in "$plugin_dir"*/; do
    [ -d "$vendor_plugin_dir" ] || continue
    plugin_name="$(basename "$vendor_plugin_dir")"
    latest=$(ls -d "$vendor_plugin_dir"*/ 2>/dev/null | sort -V | tail -1)
    [ -d "$latest" ] || continue
    skill_count=$(find "$latest" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
    agent_count=$(find "$latest" -name "AGENT.md" 2>/dev/null | wc -l | tr -d ' ')
    [ "$skill_count" -gt 0 ] || [ "$agent_count" -gt 0 ] || continue
    version=$(basename "$latest")
    plugin_rows+="| \`$plugin_name\` ($version) | $skill_count | $agent_count |"$'\n'
  done
done
if [ -n "$plugin_rows" ]; then
  printf "%s" "$plugin_rows" | sort -u
else
  echo "| (无) | — | — |"
fi

echo ""
echo "---"
echo "- **Skills** 用 \`/名称\` 调用"
echo "- **SubAgents** 用 \`@名称\` 调用"
echo "- **插件 Skills** 用 \`/插件名:skill名\` 调用（如 \`/superpowers:brainstorming\`）"
