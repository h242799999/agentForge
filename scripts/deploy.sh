#!/usr/bin/env bash
# deploy.sh — 将 agentForge 中的 Skills 和 Agents 部署到目标位置
#
# 用法：
#   ./scripts/deploy.sh --global            # 部署到 ~/.claude/（Claude Code）+ ~/.copilot/skills/（JetBrains）
#   ./scripts/deploy.sh --claude            # 仅部署到 ~/.claude/（Claude Code）
#   ./scripts/deploy.sh --copilot           # 仅部署到 ~/.copilot/skills/（JetBrains Copilot）
#   ./scripts/deploy.sh --project /path     # 部署到指定项目的 .claude/ 目录
#   ./scripts/deploy.sh --list              # 列出当前已部署的 skills/agents
#   ./scripts/deploy.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_SRC="$ROOT_DIR/skills"
AGENTS_SRC="$ROOT_DIR/agents"
GLOBAL_CLAUDE="$HOME/.claude"
COPILOT_SKILLS="$HOME/.copilot/skills"

usage() {
  echo "用法: $0 [--global | --claude | --copilot | --project <path> | --list | --help]"
  echo ""
  echo "  --global           部署到 ~/.claude/（Claude Code）+ ~/.copilot/skills/（JetBrains）"
  echo "  --claude           仅部署到 ~/.claude/（Claude Code）"
  echo "  --copilot          仅部署到 ~/.copilot/skills/（JetBrains Copilot）"
  echo "  --project <path>   部署到指定项目的 .claude/ 目录"
  echo "  --list             列出已部署的 skills 和 agents"
  echo "  --help             显示此帮助"
  exit 0
}

list_deployed() {
  echo "=== Claude Code Skills (~/.claude/skills/) ==="
  ls "$GLOBAL_CLAUDE/skills/" 2>/dev/null || echo "  (空)"
  echo ""
  echo "=== Claude Code Agents (~/.claude/agents/) ==="
  ls "$GLOBAL_CLAUDE/agents/" 2>/dev/null || echo "  (空)"
  echo ""
  echo "=== JetBrains Copilot Skills (~/.copilot/skills/) ==="
  ls "$COPILOT_SKILLS/" 2>/dev/null || echo "  (空)"
}

deploy_skills_to_claude() {
  local TARGET="$1"
  local SKILLS_DST="$TARGET/skills"
  mkdir -p "$SKILLS_DST"
  local skill_count=0
  for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name="$(basename "$skill_dir")"
    [[ "$skill_name" == "template" ]] && continue
    [[ ! -f "$skill_dir/SKILL.md" ]] && continue
    mkdir -p "$SKILLS_DST/$skill_name"
    cp -r "$skill_dir"* "$SKILLS_DST/$skill_name/"
    echo "  [Claude Skill] $skill_name → $SKILLS_DST/$skill_name/"
    skill_count=$((skill_count + 1))
  done
  echo "  已部署 $skill_count 个 Skill(s) 到 Claude Code"
}

deploy_agents_to_claude() {
  local TARGET="$1"
  local AGENTS_DST="$TARGET/agents"
  mkdir -p "$AGENTS_DST"
  local agent_count=0
  for agent_dir in "$AGENTS_SRC"/*/; do
    agent_name="$(basename "$agent_dir")"
    [[ "$agent_name" == "template" ]] && continue
    [[ ! -f "$agent_dir/AGENT.md" ]] && continue
    mkdir -p "$AGENTS_DST/$agent_name"
    cp -r "$agent_dir"* "$AGENTS_DST/$agent_name/"
    echo "  [Claude Agent] $agent_name → $AGENTS_DST/$agent_name/"
    agent_count=$((agent_count + 1))
  done
  echo "  已部署 $agent_count 个 Agent(s) 到 Claude Code"
}

deploy_skills_to_copilot() {
  mkdir -p "$COPILOT_SKILLS"
  local skill_count=0
  for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name="$(basename "$skill_dir")"
    [[ "$skill_name" == "template" ]] && continue
    [[ ! -f "$skill_dir/SKILL.md" ]] && continue
    mkdir -p "$COPILOT_SKILLS/$skill_name"
    cp -r "$skill_dir"* "$COPILOT_SKILLS/$skill_name/"
    echo "  [JetBrains Skill] $skill_name → $COPILOT_SKILLS/$skill_name/"
    skill_count=$((skill_count + 1))
  done
  echo "  已部署 $skill_count 个 Skill(s) 到 JetBrains Copilot"
}

case "${1:-}" in
  --global)
    echo "=== 部署到 Claude Code（~/.claude/）==="
    deploy_skills_to_claude "$GLOBAL_CLAUDE"
    deploy_agents_to_claude "$GLOBAL_CLAUDE"
    echo ""
    echo "=== 部署到 JetBrains Copilot（~/.copilot/skills/）==="
    deploy_skills_to_copilot
    echo ""
    echo "完成！重启 IDE 后 JetBrains Copilot 会自动加载新 Skill。"
    ;;
  --claude)
    echo "=== 部署到 Claude Code（~/.claude/）==="
    deploy_skills_to_claude "$GLOBAL_CLAUDE"
    deploy_agents_to_claude "$GLOBAL_CLAUDE"
    echo ""
    echo "完成！"
    ;;
  --copilot)
    echo "=== 部署到 JetBrains Copilot（~/.copilot/skills/）==="
    deploy_skills_to_copilot
    echo ""
    echo "完成！重启 IDE 后 JetBrains Copilot 会自动加载新 Skill。"
    ;;
  --project)
    if [[ -z "${2:-}" ]]; then
      echo "错误: --project 需要指定路径" >&2
      exit 1
    fi
    PROJECT_CLAUDE="$2/.claude"
    echo "=== 部署到项目 $PROJECT_CLAUDE ==="
    deploy_skills_to_claude "$PROJECT_CLAUDE"
    deploy_agents_to_claude "$PROJECT_CLAUDE"
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
