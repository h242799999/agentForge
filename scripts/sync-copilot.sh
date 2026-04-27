#!/usr/bin/env bash
# sync-copilot.sh — 将 Skills 和 Agents 的核心描述同步到 .github/copilot-instructions.md
#                   实现 Claude Code 和 GitHub Copilot 的跨工具复用
#
# 用法: ./scripts/sync-copilot.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT="$ROOT_DIR/.github/copilot-instructions.md"

mkdir -p "$ROOT_DIR/.github"

cat > "$OUTPUT" << 'HEADER'
# Copilot 自定义指令
# 由 sync-copilot.sh 自动生成 — 请勿手动编辑此文件
# 源文件在 skills/ 和 agents/ 目录

此项目使用 skill-workshop 开发的自定义 Skills 和 Agents。
以下是项目中定义的工作流程和专项能力，请在相关场景中遵循这些规范。

HEADER

# 提取所有 Skill 的描述和内容
echo "## Skills（工作流程）" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for skill_dir in "$ROOT_DIR/skills"/*/; do
  skill_name="$(basename "$skill_dir")"
  if [[ "$skill_name" == "template" ]]; then continue; fi
  skill_md="$skill_dir/SKILL.md"
  if [[ ! -f "$skill_md" ]]; then continue; fi

  # 提取 description 字段
  desc=$(grep -m1 "^description:" "$skill_md" | sed 's/^description: *//' || echo "")
  echo "### $skill_name" >> "$OUTPUT"
  echo "$desc" >> "$OUTPUT"
  echo "" >> "$OUTPUT"

  # 提取正文（去掉 frontmatter）
  awk '/^---/{p++; next} p>=2{print}' "$skill_md" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
done

# 提取所有 Agent 的描述
echo "## Agents（专项分析）" >> "$OUTPUT"
echo "" >> "$OUTPUT"

for agent_file in "$ROOT_DIR/agents"/*.md; do
  agent_name="$(basename "$agent_file" .md)"
  if [[ "$agent_name" == "template" ]]; then continue; fi

  desc=$(grep -m1 "^description:" "$agent_file" | sed 's/^description: *//' || echo "")
  echo "### $agent_name" >> "$OUTPUT"
  echo "$desc" >> "$OUTPUT"
  echo "" >> "$OUTPUT"

  awk '/^---/{p++; next} p>=2{print}' "$agent_file" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
done

echo "已生成: $OUTPUT"
echo "提示: 将此文件提交到 Git，GitHub Copilot 会自动读取。"
