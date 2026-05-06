"""jsonl 索引和历史记录的删除辅助函数。"""

from __future__ import annotations

from pathlib import Path

from config import SESSION_INDEX_PATH
from codex_store.sessions import load_session_index, write_jsonl

def _remove_session_from_history(path: Path, session_ids: set[str]) -> None:
    if not path.exists():
        return
    kept_lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not any(f'"session_id":"{session_id}"' in line for session_id in session_ids)
    ]
    path.write_text("\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8")


def _remove_session_from_index(path: Path, session_ids: set[str]) -> None:
    if not path.exists():
        return
    rows = [row for row in load_session_index() if str(row.get("id", "")).strip() not in session_ids] if path == SESSION_INDEX_PATH else []
    if path != SESSION_INDEX_PATH:
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("id", "")).strip() not in session_ids:
                rows.append(row)
    write_jsonl(path, rows)

