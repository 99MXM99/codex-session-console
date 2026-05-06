"""桌面系统动作。"""

from __future__ import annotations

import json
import platform
import shlex
import shutil
import subprocess

from codex_store.store import load_sessions


def open_selected_sessions(session_ids: list[str]) -> str:
    """在本机终端里批量恢复已选会话。"""

    selected_ids = list(dict.fromkeys(session_id.strip() for session_id in session_ids if session_id.strip()))
    if not selected_ids:
        return "请先选择要开启的会话。"

    existing_ids = {record.id for record in load_sessions() if record.exists}
    resumable_ids = [session_id for session_id in selected_ids if session_id in existing_ids]
    if not resumable_ids:
        return "没有可继续的已选会话。"

    system_name = platform.system()
    for session_id in resumable_ids:
        command = f"cdx resume {shlex.quote(session_id)}"
        if system_name == "Darwin":
            script = f'tell application "Terminal" to do script {json.dumps(command)}'
            subprocess.Popen(["osascript", "-e", script])
        elif system_name == "Linux":
            terminal = _find_linux_terminal()
            if not terminal:
                raise RuntimeError("没有找到可用的 Linux 终端程序。")
            subprocess.Popen([terminal, "-e", "bash", "-lc", command])
        else:
            raise RuntimeError(f"当前系统不支持自动开启会话：{system_name}")

    return f"已尝试开启 {len(resumable_ids)} 条会话。"


def _find_linux_terminal() -> str | None:
    """查找常见 Linux 终端命令，供桌面入口批量开启会话。"""

    for name in ("x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "xterm"):
        path = shutil.which(name)
        if path:
            return path
    return None
