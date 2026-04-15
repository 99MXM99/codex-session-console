"""项目级配置常量。

集中放路径、默认输出位置、时区和主题配置，避免散落在各个模块里。
"""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo


CODEX_DIR = Path.home() / ".codex"
DB_PATH = CODEX_DIR / "state_5.sqlite"
SESSION_INDEX_PATH = CODEX_DIR / "session_index.jsonl"
HISTORY_PATH = CODEX_DIR / "history.jsonl"
BACKUP_DIR = CODEX_DIR / "session_manager_backups"
DEFAULT_TXT_OUTPUT = Path.home() / "Documents" / "codex_session_export.txt"
DEFAULT_JSON_OUTPUT = Path.home() / "Documents" / "codex_session_export.json"
TZ = ZoneInfo("Asia/Shanghai")

THEMES: dict[str, dict[str, str]] = {
    "apple": {
        "bg": "#eef2f7",
        "panel": "#ffffff",
        "ink": "#111111",
        "muted": "#6e6e73",
        "line": "#d2d2d7",
        "accent": "#0071e3",
        "accent_2": "#2997ff",
        "danger": "#d63f32",
    },
    "paper": {
        "bg": "#f4efe7",
        "panel": "#fffbf5",
        "ink": "#1f1d1a",
        "muted": "#6d665c",
        "line": "#ddd1c1",
        "accent": "#8f4a28",
        "accent_2": "#1e5a52",
        "danger": "#8a3b2e",
    },
    "cohere": {
        "bg": "#ffffff",
        "panel": "#fafafa",
        "ink": "#000000",
        "muted": "#93939f",
        "line": "#d9d9dd",
        "accent": "#1863dc",
        "accent_2": "#9b60aa",
        "danger": "#d94a38",
    },
    "lamborghini": {
        "bg": "#0d0d0f",
        "panel": "#17181c",
        "ink": "#f6f1de",
        "muted": "#b3ab92",
        "line": "#383322",
        "accent": "#f6c300",
        "accent_2": "#ffdf66",
        "danger": "#d94a38",
    },
}
