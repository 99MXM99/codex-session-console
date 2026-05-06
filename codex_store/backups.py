"""备份扫描、可恢复性判断和 rollout 备份。"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import sqlite3
from pathlib import Path

from config import BACKUP_DIR, TZ
from models import SessionRecord

SESSION_FILE_MAP_NAME = "session_files.json"

def ensure_backup(paths: list[Path]) -> Path:
    """在危险操作前备份底层数据。"""

    stamp = dt.datetime.now(TZ).strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / stamp
    target.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, target / path.name)
    return target


def _session_files_map_path(backup_dir: Path) -> Path:
    return backup_dir / SESSION_FILE_MAP_NAME


def _load_session_file_map(backup_dir: Path) -> dict[str, dict[str, str]]:
    mapping_path = _session_files_map_path(backup_dir)
    if not mapping_path.exists():
        return {}
    try:
        return json.loads(mapping_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_session_file_map(backup_dir: Path, mapping: dict[str, dict[str, str]]) -> None:
    _session_files_map_path(backup_dir).write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def backup_session_rollouts(backup_dir: Path, records: list[SessionRecord]) -> None:
    """把待删除会话的原始 rollout 文件一起备份下来。"""

    sessions_dir = backup_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    mapping = _load_session_file_map(backup_dir)

    for record in records:
        if not record.rollout_path:
            continue
        source = Path(record.rollout_path)
        if not source.exists():
            continue
        backup_name = f"{record.id}{source.suffix or '.jsonl'}"
        target = sessions_dir / backup_name
        shutil.copy2(source, target)
        mapping[record.id] = {
            "rollout_path": str(source),
            "backup_name": backup_name,
        }

    if mapping:
        _write_session_file_map(backup_dir, mapping)


def list_backups() -> list[Path]:
    if not BACKUP_DIR.exists():
        return []
    return sorted(
        [path for path in BACKUP_DIR.iterdir() if path.is_dir()],
        key=lambda p: p.name,
        reverse=True,
    )


def load_recoverable_session_ids() -> set[str]:
    """扫描全部备份，找出理论上可恢复的会话 ID。

    判断标准是：备份里既有该会话的元数据，也有对应的 rollout 文件。
    """

    recoverable_ids: set[str] = set()
    for backup_dir in list_backups():
        file_map = _load_session_file_map(backup_dir)
        if not file_map:
            continue

        db_backup = backup_dir / "state_5.sqlite"
        candidate_ids: set[str] = set()
        if db_backup.exists():
            try:
                conn = sqlite3.connect(db_backup)
                rows = conn.execute("select id from threads where source = 'cli'").fetchall()
                conn.close()
                candidate_ids.update(str(row[0]) for row in rows if row and row[0])
            except sqlite3.Error:
                pass

        index_backup = backup_dir / "session_index.jsonl"
        if index_backup.exists():
            try:
                for line in index_backup.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    session_id = str(row.get("id", "")).strip()
                    if session_id:
                        candidate_ids.add(session_id)
            except (OSError, json.JSONDecodeError):
                pass

        for session_id, file_info in file_map.items():
            backup_name = file_info.get("backup_name", "")
            if session_id in candidate_ids and backup_name and (backup_dir / "sessions" / backup_name).exists():
                recoverable_ids.add(session_id)

    return recoverable_ids


def find_backup_for_session(session_id: str) -> Path | None:
    """找到包含指定会话的最近一份备份。

    当前恢复能力仍是整库恢复，这里只是帮 UI 找到“按这条记录触发恢复”时要用哪份备份。
    """

    clean_id = session_id.strip()
    if not clean_id:
        return None

    recoverable_ids = load_recoverable_session_ids()
    if clean_id not in recoverable_ids:
        return None

    for backup_dir in list_backups():
        file_map = _load_session_file_map(backup_dir)
        file_info = file_map.get(clean_id)
        if not file_info:
            continue
        backup_name = file_info.get("backup_name", "")
        if backup_name and (backup_dir / "sessions" / backup_name).exists():
            return backup_dir

    return None

