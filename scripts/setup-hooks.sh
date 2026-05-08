#!/usr/bin/env bash
# setup-hooks.sh — 安装 git post-commit hook，在每次 commit 后自动部署 skills
#
# 用法：运行一次即可
#   bash scripts/setup-hooks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_DIR="$(git -C "$ROOT_DIR" rev-parse --absolute-git-dir)"
HOOK_FILE="$GIT_DIR/hooks/post-commit"
mkdir -p "$GIT_DIR/hooks"
DEPLOY_SCRIPT="$SCRIPT_DIR/deploy.sh"

if [[ -f "$HOOK_FILE" ]]; then
  echo "警告：$HOOK_FILE 已存在，将备份为 post-commit.bak"
  cp "$HOOK_FILE" "${HOOK_FILE}.bak"
fi

cat > "$HOOK_FILE" <<EOF
#!/usr/bin/env bash
echo "[agentForge] 检测到 commit，自动部署 skills 到三个平台..."
bash "$DEPLOY_SCRIPT" --global
EOF

chmod +x "$HOOK_FILE"
echo "✓ git post-commit hook 已安装：$HOOK_FILE"
echo "  每次 git commit 后将自动部署到 ~/.claude / ~/.copilot / ~/.cursor"
