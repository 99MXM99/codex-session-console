"""会话重命名、删除、彻底删除和恢复。"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import sqlite3
from pathlib import Path

from config import DB_PATH, HISTORY_PATH, SESSION_INDEX_PATH, BACKUP_DIR
from codex_store.backups import _load_session_file_map, _session_files_map_path, _write_session_file_map, backup_session_rollouts, ensure_backup, find_backup_for_session, list_backups
from codex_store.jsonl_utils import _remove_session_from_history, _remove_session_from_index
from codex_store.sessions import load_session_index, load_sessions, write_jsonl
from codex_store.sqlite_utils import _delete_thread_rows_by_scan, _rebuild_threads_table, _remove_session_from_db, _remove_single_session_from_current_db

def _purge_backup_traces(session_ids: set[str]) -> tuple[int, int]:
    """从所有备份目录里删掉指定会话的元数据和原始文件痕迹。"""

    touched_backups = 0
    removed_rollouts = 0
    for backup_dir in list_backups():
        touched = False
        file_map = _load_session_file_map(backup_dir)
        if file_map:
            sessions_dir = backup_dir / "sessions"
            for session_id in list(session_ids):
                file_info = file_map.pop(session_id, None)
                if not file_info:
                    continue
                backup_name = file_info.get("backup_name", "")
                if backup_name:
                    backup_file = sessions_dir / backup_name
                    if backup_file.exists():
                        backup_file.unlink()
                        removed_rollouts += 1
                touched = True
            mapping_path = _session_files_map_path(backup_dir)
            if file_map:
                _write_session_file_map(backup_dir, file_map)
            elif mapping_path.exists():
                mapping_path.unlink()
            if sessions_dir.exists() and not any(sessions_dir.iterdir()):
                sessions_dir.rmdir()

        index_backup = backup_dir / "session_index.jsonl"
        if index_backup.exists():
            before = index_backup.read_text(encoding="utf-8")
            _remove_session_from_index(index_backup, session_ids)
            if index_backup.read_text(encoding="utf-8") != before:
                touched = True

        history_backup = backup_dir / "history.jsonl"
        if history_backup.exists():
            before = history_backup.read_text(encoding="utf-8")
            _remove_session_from_history(history_backup, session_ids)
            if history_backup.read_text(encoding="utf-8") != before:
                touched = True

        db_backup = backup_dir / "state_5.sqlite"
        if db_backup.exists():
            try:
                conn = sqlite3.connect(db_backup)
                try:
                    changed = _delete_thread_rows_by_scan(conn, session_ids) > 0
                    if changed:
                        touched = True
                finally:
                    conn.close()
            except sqlite3.Error:
                try:
                    _rebuild_threads_table(db_backup)
                    conn = sqlite3.connect(db_backup)
                    try:
                        changed = _delete_thread_rows_by_scan(conn, session_ids) > 0
                        if changed:
                            touched = True
                    finally:
                        conn.close()
                except sqlite3.Error:
                    # 某些历史备份库可能已经损坏，不阻断当前会话的彻底删除。
                    pass

        if touched:
            touched_backups += 1

    return touched_backups, removed_rollouts


def restore_backup(backup_name: str) -> str:
    """从指定备份目录恢复关键数据文件。"""

    backup_dir = BACKUP_DIR / backup_name
    if not backup_dir.exists() or not backup_dir.is_dir():
        return "未找到可恢复的备份。"

    mapping = {
        "history.jsonl": HISTORY_PATH,
        "session_index.jsonl": SESSION_INDEX_PATH,
        "state_5.sqlite": DB_PATH,
    }
    restored: list[str] = []
    for filename, target in mapping.items():
        source = backup_dir / filename
        if source.exists():
            shutil.copy2(source, target)
            restored.append(filename)

    if not restored:
        return "备份目录存在，但没有可恢复的数据文件。"
    return f"已从备份 {backup_name} 恢复：{', '.join(restored)}"


def restore_session(session_id: str) -> str:
    """按会话恢复必要元数据和 rollout 文件。"""

    clean_id = session_id.strip()
    backup_dir = find_backup_for_session(clean_id)
    if not backup_dir:
        return f"未找到包含会话 {clean_id} 的可用备份。"

    file_map = _load_session_file_map(backup_dir)
    file_info = file_map.get(clean_id, {})
    backup_name = file_info.get("backup_name", "")
    original_rollout_path = file_info.get("rollout_path", "")
    rollout_backup = backup_dir / "sessions" / backup_name
    if not backup_name or not original_rollout_path or not rollout_backup.exists():
        return f"会话 {clean_id} 缺少可恢复的原始文件。"

    backup_db = backup_dir / "state_5.sqlite"
    if not backup_db.exists():
        return f"会话 {clean_id} 缺少可恢复的数据库备份。"

    ensure_backup([HISTORY_PATH, SESSION_INDEX_PATH, DB_PATH])
    _rebuild_threads_table(DB_PATH)

    backup_conn = sqlite3.connect(backup_db)
    backup_conn.row_factory = sqlite3.Row
    row = backup_conn.execute("select * from threads where id = ? limit 1", (clean_id,)).fetchone()
    backup_conn.close()
    if not row:
        return f"备份中找不到会话 {clean_id} 的线程记录。"

    columns = list(row.keys())
    placeholders = ", ".join(["?"] * len(columns))
    column_list = ", ".join(columns)
    values = [row[column] for column in columns]

    _remove_single_session_from_current_db(clean_id)
    current_conn = sqlite3.connect(DB_PATH)
    current_conn.execute(
        f"insert into threads ({column_list}) values ({placeholders})",
        values,
    )
    current_conn.commit()
    current_conn.close()

    backup_index = backup_dir / "session_index.jsonl"
    if backup_index.exists():
        backup_rows = []
        for line in backup_index.read_text(encoding="utf-8").splitlines():
            if line.strip():
                backup_rows.append(json.loads(line))
        current_rows = load_session_index()
        replacement = next((item for item in backup_rows if str(item.get("id", "")).strip() == clean_id), None)
        if replacement:
            current_rows = [item for item in current_rows if str(item.get("id", "")).strip() != clean_id]
            current_rows.append(replacement)
            write_jsonl(SESSION_INDEX_PATH, current_rows)

    backup_history = backup_dir / "history.jsonl"
    if backup_history.exists():
        existing_lines = HISTORY_PATH.read_text(encoding="utf-8").splitlines() if HISTORY_PATH.exists() else []
        restored_lines = [
            line
            for line in backup_history.read_text(encoding="utf-8").splitlines()
            if f'"session_id":"{clean_id}"' in line and line not in existing_lines
        ]
        if restored_lines:
            HISTORY_PATH.write_text(
                "\n".join(existing_lines + restored_lines) + "\n",
                encoding="utf-8",
            )

    rollout_target = Path(original_rollout_path)
    rollout_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rollout_backup, rollout_target)

    return f"已恢复会话 {clean_id}。"


def delete_sessions(session_ids: list[str]) -> str:
    """批量删除会话，并同步清理对应 rollout 文件。

    这里保留 threads 表中的元数据，用于在“已删除 / 全部会话”视图中继续展示。
    """

    clean_ids = [session_id.strip() for session_id in session_ids if session_id.strip()]
    if not clean_ids:
        return "请先选择要删除的会话。"

    backup_dir = ensure_backup([HISTORY_PATH, SESSION_INDEX_PATH, DB_PATH])
    records = {item.id: item for item in load_sessions()}
    backup_session_rollouts(backup_dir, [record for session_id, record in records.items() if session_id in clean_ids])

    session_id_set = set(clean_ids)
    _remove_session_from_history(HISTORY_PATH, session_id_set)

    index_rows = [row for row in load_session_index() if str(row.get("id", "")).strip() not in session_id_set]
    write_jsonl(SESSION_INDEX_PATH, index_rows)

    removed_files = 0
    for session_id in clean_ids:
        record = records.get(session_id)
        if record and record.rollout_path:
            rollout_path = Path(record.rollout_path)
            if rollout_path.exists():
                rollout_path.unlink()
                removed_files += 1

    return f"已删除 {len(clean_ids)} 条会话，清理 {removed_files} 个会话文件。备份已保存到 {backup_dir}"


def hard_delete_sessions(session_ids: list[str]) -> str:
    """彻底删除会话，并同步清理当前数据与所有备份中的痕迹。"""

    clean_ids = [session_id.strip() for session_id in session_ids if session_id.strip()]
    if not clean_ids:
        return "请先选择要彻底删除的会话。"

    session_id_set = set(clean_ids)
    records = {item.id: item for item in load_sessions()}

    _rebuild_threads_table(DB_PATH)
    _remove_session_from_history(HISTORY_PATH, session_id_set)
    _remove_session_from_index(SESSION_INDEX_PATH, session_id_set)
    _remove_session_from_db(DB_PATH, session_id_set)

    removed_live_rollouts = 0
    for session_id in session_id_set:
        record = records.get(session_id)
        if record and record.rollout_path:
            rollout_path = Path(record.rollout_path)
            if rollout_path.exists():
                rollout_path.unlink()
                removed_live_rollouts += 1

    touched_backups, removed_backup_rollouts = _purge_backup_traces(session_id_set)
    total_removed_rollouts = removed_live_rollouts + removed_backup_rollouts

    remaining_ids = {item.id for item in load_sessions()}
    not_removed = sorted(session_id for session_id in session_id_set if session_id in remaining_ids)
    if not_removed:
        raise RuntimeError(
            "彻底删除未完成，以下会话仍然存在于当前 Codex 数据中："
            + ", ".join(not_removed)
        )

    return (
        f"已彻底删除 {len(session_id_set)} 条会话，"
        f"清理 {total_removed_rollouts} 个会话文件，"
        f"同步更新 {touched_backups} 份备份。"
    )


def rename_session(session_id: str, new_name: str) -> str:
    """设置管理器内的自定义标题，不覆盖 Codex 原生标题。"""

    clean_name = new_name.strip()
    if not clean_name:
        return "新标题不能为空。"

    backup_dir = ensure_backup([SESSION_INDEX_PATH])
    rows = load_session_index()
    found = False
    for row in rows:
        if str(row.get("id", "")) == session_id:
            row["thread_name"] = clean_name
            row["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            found = True
            break

    if not found:
        rows.append({"id": session_id, "thread_name": clean_name, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()})

    write_jsonl(SESSION_INDEX_PATH, rows)
    return f"已设置标题 {session_id}。备份已保存到 {backup_dir}"
