#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="${1:-}"
HOST="${2:-127.0.0.1}"
PORT="${3:-8876}"
OPEN_MODE="${4:-open}"
LOG_FILE="${5:-/tmp/codex-session-console.log}"

if [ -z "$PROJECT_DIR" ] || [ ! -d "$PROJECT_DIR" ]; then
  echo "找不到项目目录：$PROJECT_DIR" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "系统里没有可用的 python3。" >&2
  exit 1
fi

if ! command -v lsof >/dev/null 2>&1; then
  echo "系统里没有可用的 lsof。" >&2
  exit 1
fi

LOG_DIR="$(dirname "$LOG_FILE")"
mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"

PORT_PID="$(lsof -tiTCP:${PORT} -sTCP:LISTEN 2>/dev/null || true)"
if [ -n "$PORT_PID" ]; then
  kill "$PORT_PID" 2>/dev/null || true
  sleep 1
fi

nohup env PYTHONUNBUFFERED=1 python3 app.py --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &

open_url() {
  local url="$1"
  case "$(uname -s)" in
    Darwin)
      if command -v open >/dev/null 2>&1; then
        open "$url" >/dev/null 2>&1 &
      fi
      ;;
    Linux)
      if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$url" >/dev/null 2>&1 &
      fi
      ;;
  esac
}

for _ in 1 2 3 4 5; do
  if lsof -tiTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
    if [ "$OPEN_MODE" = "open" ]; then
      open_url "http://${HOST}:${PORT}/?_ts=$(date +%s)"
    fi
    exit 0
  fi
  sleep 1
done

echo "服务没有成功启动。日志位置：$LOG_FILE" >&2
exit 1
