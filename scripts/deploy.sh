#!/usr/bin/env bash
# deploy.sh — 将 skill-workshop 中的 Skills 和 Agents 部署到目标位置
#
# 用法：
#   ./scripts/deploy.sh --global            # 部署到 ~/.claude/（用户级，所有项目可用）
#   ./scripts/deploy.sh --project /path     # 部署到指定项目的 .claude/ 目录
#   ./scripts/deploy.sh --list              # 列出当前已部署的 skills/agents
#   ./scripts/deploy.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_SRC="$ROOT_DIR/skills"
AGENTS_SRC="$ROOT_DIR/agents"
GLOBAL_CLAUDE="$HOME/.claude"

usage() {
  echo "用法: $0 [--global | --project <path> | --list | --help]"
  echo ""
  echo "  --global           部署到 ~/.claude/（全局，所有项目可用）"
  echo "  --project <path>   部署到指定项目的 .claude/ 目录"
  echo "  --list             列出已部署的 skills 和 agents"
  echo "  --help             显示此帮助"
  exit 0
}

list_deployed() {
  echo "=== 全局 Skills (~/.claude/skills/) ==="
  ls "$GLOBAL_CLAUDE/skills/" 2>/dev/null || echo "  (空)"
  echo ""
  echo "=== 全局 Agents (~/.claude/agents/) ==="
  ls "$GLOBAL_CLAUDE/agents/" 2>/dev/null || echo "  (空)"
}

deploy_to() {
  local TARGET="$1"
  local SKILLS_DST="$TARGET/skills"
  local AGENTS_DST="$TARGET/agents"

  echo "目标目录: $TARGET"
  echo ""

  # 部署 Skills
  mkdir -p "$SKILLS_DST"
  local skill_count=0
  for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name="$(basename "$skill_dir")"
    # 跳过 template
    if [[ "$skill_name" == "template" ]]; then continue; fi
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
      echo "  [跳过] $skill_name — 缺少 SKILL.md"
      continue
    fi
    mkdir -p "$SKILLS_DST/$skill_name"
    cp -r "$skill_dir"* "$SKILLS_DST/$skill_name/"
    echo "  [Skill] $skill_name → $SKILLS_DST/$skill_name/"
    skill_count=$((skill_count + 1))
  done
  echo "  已部署 $skill_count 个 Skill(s)"
  echo ""

  # 部署 Agents
  mkdir -p "$AGENTS_DST"
  local agent_count=0
  for agent_file in "$AGENTS_SRC"/*.md; do
    agent_name="$(basename "$agent_file" .md)"
    # 跳过 template
    if [[ "$agent_name" == "template" ]]; then continue; fi
    cp "$agent_file" "$AGENTS_DST/$agent_name.md"
    echo "  [Agent] $agent_name → $AGENTS_DST/$agent_name.md"
    agent_count=$((agent_count + 1))
  done
  echo "  已部署 $agent_count 个 Agent(s)"
}

# 解析参数
case "${1:-}" in
  --global)
    echo "=== 部署到全局 ~/.claude/ ==="
    deploy_to "$GLOBAL_CLAUDE"
    echo ""
    echo "完成！Claude Code 会自动加载这些 Skills 和 Agents。"
    ;;
  --project)
    if [[ -z "${2:-}" ]]; then
      echo "错误: --project 需要指定路径" >&2
      exit 1
    fi
    PROJECT_CLAUDE="$2/.claude"
    echo "=== 部署到项目 $PROJECT_CLAUDE ==="
    deploy_to "$PROJECT_CLAUDE"
    echo ""
    echo "完成！在该项目中使用 Claude Code 时会自动加载。"
    ;;
  --list)
    list_deployed
    ;;
  --help|"")
    usage
    ;;
  *)
    echo "未知参数: $1" >&2
    usage
    ;;
esac
