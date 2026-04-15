#!/bin/zsh

set -euo pipefail

# 基于启动器自身所在目录运行，避免依赖固定绝对路径。
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/tools/run_local_ui.sh" "$SCRIPT_DIR" "127.0.0.1" "8876" "open" "/tmp/codex-session-console.log"
