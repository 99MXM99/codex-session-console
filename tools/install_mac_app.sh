#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="Codex Session Console.app"
DESKTOP_APP_DIR="$HOME/Desktop/$APP_NAME"
ICON_FILE="$PROJECT_DIR/macos/AppIcon.icns"
TEMP_ROOT="$(mktemp -d /tmp/codex-session-console-app.XXXXXX)"
APP_DIR="$TEMP_ROOT/$APP_NAME"
MACOS_DIR="$APP_DIR/Contents/MacOS"
RESOURCES_DIR="$APP_DIR/Contents/Resources"

cleanup() {
  /bin/rm -rf "$TEMP_ROOT"
}

trap cleanup EXIT

if [ ! -f "$PROJECT_DIR/macos/Info.plist" ] || [ ! -f "$PROJECT_DIR/macos/launcher.sh.template" ]; then
  printf '缺少 macOS 打包模板文件。\n' >&2
  exit 1
fi

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

/bin/cp "$PROJECT_DIR/macos/Info.plist" "$APP_DIR/Contents/Info.plist"
/usr/bin/sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$PROJECT_DIR/macos/launcher.sh.template" > "$MACOS_DIR/launch"
/bin/chmod +x "$MACOS_DIR/launch"

if [ -f "$ICON_FILE" ]; then
  /bin/cp "$ICON_FILE" "$RESOURCES_DIR/AppIcon.icns"
fi

/bin/rm -rf "$DESKTOP_APP_DIR"
/bin/cp -R "$APP_DIR" "$DESKTOP_APP_DIR"

printf '已生成桌面应用：%s\n' "$DESKTOP_APP_DIR"
