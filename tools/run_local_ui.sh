#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="${1:-}"
HOST="${2:-127.0.0.1}"
PORT="${3:-8876}"
OPEN_MODE="${4:-open}"
LOG_FILE="${5:-/tmp/codex-session-console.log}"
PID_FILE="${6:-/tmp/codex-session-console.pid}"

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

listener_pids() {
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true
}

has_listener_pid() {
  local target_pid="$1"
  for pid in $(listener_pids); do
    if [ "$pid" = "$target_pid" ]; then
      return 0
    fi
  done
  return 1
}

wait_for_listener() {
  local attempts="$1"
  for _ in $(seq 1 "$attempts"); do
    if [ -n "$(listener_pids)" ]; then
      return 0
    fi
    sleep 0.1
  done
  return 1
}

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

PORT_PIDS="$(listener_pids)"
if [ -n "$PORT_PIDS" ]; then
  known_pid=""
  if [ -f "$PID_FILE" ]; then
    known_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  fi

  if [ -n "$known_pid" ] && has_listener_pid "$known_pid"; then
    if [ "$OPEN_MODE" = "open" ]; then
      open_url "http://${HOST}:${PORT}/?_ts=$(date +%s)"
    fi
    exit 0
  fi

  if [ "$(printf '%s\n' "$PORT_PIDS" | wc -l | tr -d ' ')" = "1" ]; then
    printf '%s\n' "$PORT_PIDS" >"$PID_FILE"
    if [ "$OPEN_MODE" = "open" ]; then
      open_url "http://${HOST}:${PORT}/?_ts=$(date +%s)"
    fi
    exit 0
  fi

  echo "端口 ${PORT} 已被其他进程占用，无法自动启动。日志位置：$LOG_FILE" >&2
  exit 1
fi

nohup env PYTHONUNBUFFERED=1 python3 app.py --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
SERVER_PID=$!
printf '%s\n' "$SERVER_PID" >"$PID_FILE"

if wait_for_listener 30; then
  if [ "$OPEN_MODE" = "open" ]; then
    open_url "http://${HOST}:${PORT}/?_ts=$(date +%s)"
  fi
  exit 0
fi

rm -f "$PID_FILE"
echo "服务没有成功启动。日志位置：$LOG_FILE" >&2
exit 1
