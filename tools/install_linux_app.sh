#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
APPLICATIONS_DIR="${HOME}/.local/share/applications"
DESKTOP_DIR="${HOME}/Desktop"
LAUNCHER_PATH="${BIN_DIR}/codex-session-console"
DESKTOP_FILE_PATH="${APPLICATIONS_DIR}/codex-session-console.desktop"
DESKTOP_SHORTCUT_PATH="${DESKTOP_DIR}/Codex Session Console.desktop"
ICON_PATH="${PROJECT_DIR}/linux/AppIcon.svg"

mkdir -p "$BIN_DIR" "$APPLICATIONS_DIR"

if [ ! -f "$PROJECT_DIR/linux/launcher.sh.template" ] || [ ! -f "$PROJECT_DIR/linux/codex-session-console.desktop.template" ]; then
  printf '缺少 Linux 启动模板文件。\n' >&2
  exit 1
fi

sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$PROJECT_DIR/linux/launcher.sh.template" > "$LAUNCHER_PATH"
chmod +x "$LAUNCHER_PATH"

sed \
  -e "s|__EXEC_PATH__|$LAUNCHER_PATH|g" \
  -e "s|__ICON_PATH__|$ICON_PATH|g" \
  -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  "$PROJECT_DIR/linux/codex-session-console.desktop.template" > "$DESKTOP_FILE_PATH"

chmod +x "$DESKTOP_FILE_PATH"

if [ -d "$DESKTOP_DIR" ]; then
  cp "$DESKTOP_FILE_PATH" "$DESKTOP_SHORTCUT_PATH"
  chmod +x "$DESKTOP_SHORTCUT_PATH"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

printf '已安装 Linux 启动器：%s\n' "$LAUNCHER_PATH"
printf '已安装 Linux 桌面入口：%s\n' "$DESKTOP_FILE_PATH"

if [ -d "$DESKTOP_DIR" ]; then
  printf '桌面快捷方式：%s\n' "$DESKTOP_SHORTCUT_PATH"
fi
