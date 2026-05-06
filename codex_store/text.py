"""时间和主题配置辅助函数。"""

from __future__ import annotations

import datetime as dt

from config import THEMES, TZ


def format_ts(ts: int) -> str:
    """按本项目固定时区格式化 Codex 会话时间。"""

    return dt.datetime.fromtimestamp(ts, TZ).strftime("%Y-%m-%d %H:%M:%S")


def resolve_theme(theme: str) -> tuple[str, dict[str, str]]:
    """解析页面主题，不存在时回退到 paper。"""

    chosen = theme if theme in THEMES else "paper"
    return chosen, THEMES[chosen]
