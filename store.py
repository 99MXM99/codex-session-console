"""Codex 本地数据读写层。

这里封装所有对 SQLite、jsonl 和备份目录的访问，避免 UI 和 HTTP 层直接碰底层文件。
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import sqlite3
from dataclasses import asdict
from math import ceil
from pathlib import Path
from typing import Any

from config import BACKUP_DIR, DB_PATH, DEFAULT_JSON_OUTPUT, DEFAULT_TXT_OUTPUT, HISTORY_PATH, SESSION_INDEX_PATH, THEMES, TZ
from models import SessionRecord

SESSION_FILE_MAP_NAME = "session_files.json"


def shorten_text(text: str, max_len: int = 36) -> str:
    """把较长首句压缩成适合列表展示的短主题。"""

    text = text.strip()
    if len(text) <= max_len:
        return text
    for sep in ["。", "！", "？", "；", "，", ",", ":", "："]:
        idx = text.find(sep)
        if 8 <= idx <= max_len:
            return text[:idx].strip()
    return text[: max_len - 3].rstrip() + "..."


def derive_theme(text: str) -> str:
    """从首条用户消息提炼短主题。"""

    raw = (text or "").strip()
    if not raw:
        return ""
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return ""
    for line in lines:
        for prefix in ("主题：", "Topic:", "Task:", "Task：", "主题:"):
            if line.startswith(prefix):
                return shorten_text(line.split(prefix, 1)[1].strip())
    for line in lines:
        lowered = line.lower()
        if lowered.startswith(("role:", "project layout", "technical constraints")):
            continue
        return shorten_text(line)
    return shorten_text(lines[0])


def format_ts(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, TZ).strftime("%Y-%m-%d %H:%M:%S")


def resolve_theme(theme: str) -> tuple[str, dict[str, str]]:
    chosen = theme if theme in THEMES else "paper"
    return chosen, THEMES[chosen]


def load_session_index() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not SESSION_INDEX_PATH.exists():
        return rows
    for line in SESSION_INDEX_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    content = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(content + ("\n" if content else ""), encoding="utf-8")


def load_thread_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for row in load_session_index():
        session_id = str(row.get("id", "")).strip()
        thread_name = str(row.get("thread_name", "")).strip()
        if session_id:
            names[session_id] = thread_name
    return names


def load_sessions() -> list[SessionRecord]:
    """从 Codex 本地数据库和索引文件构造会话列表。"""

    if not DB_PATH.exists():
        return []

    names = load_thread_names()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        select id, created_at, first_user_message, title, rollout_path
        from threads
        where source = 'cli'
        order by created_at desc
        """
    ).fetchall()
    conn.close()

    sessions: list[SessionRecord] = []
    for row in rows:
        rollout_path = str(row["rollout_path"] or "")
        exists = bool(rollout_path and os.path.exists(rollout_path))
        first_user_raw = str(row["first_user_message"] or "").strip()
        theme = derive_theme(first_user_raw)
        thread_name = names.get(str(row["id"]), str(row["title"] or "")).strip()
        renamed_title = thread_name if thread_name and thread_name != first_user_raw else "未设置标题"
        sessions.append(
            SessionRecord(
                id=str(row["id"]),
                created_at=int(row["created_at"]),
                created_at_text=format_ts(int(row["created_at"])),
                theme=theme,
                thread_name=thread_name,
                renamed_title=renamed_title,
                rollout_path=rollout_path,
                exists=exists,
            )
        )
    return sessions


def filter_sessions(records: list[SessionRecord], query: str) -> list[SessionRecord]:
    q = query.strip().lower()
    if not q:
        return records
    return [
        record
        for record in records
        if q in record.id.lower()
        or q in record.theme.lower()
        or q in record.thread_name.lower()
        or q in record.renamed_title.lower()
    ]


def filter_by_status(records: list[SessionRecord], status: str) -> list[SessionRecord]:
    if status == "existing":
        return [record for record in records if record.exists]
    if status == "deleted":
        return [record for record in records if not record.exists]
    return records


def paginate_records(records: list[SessionRecord], page: int, page_size: int) -> tuple[list[SessionRecord], int, int]:
    safe_page_size = max(10, min(page_size, 100))
    total_pages = max(1, ceil(len(records) / safe_page_size)) if records else 1
    safe_page = max(1, min(page, total_pages))
    start = (safe_page - 1) * safe_page_size
    end = start + safe_page_size
    return records[start:end], safe_page, total_pages


def export_txt(records: list[SessionRecord], output_path: Path | None = None) -> Path:
    output = output_path or DEFAULT_TXT_OUTPUT
    lines = [
        "Codex 对话记录",
        f"生成时间：{dt.datetime.now(TZ).strftime('%Y-%m-%d')}",
        "",
    ]
    for idx, record in enumerate(records, start=1):
        lines.extend(
            [
                f"{idx}.",
                f"编号：{record.id}",
                f"时间：{record.created_at_text}（Asia/Shanghai）",
                f"主题：{record.theme}",
                f"重命名的标题：{record.renamed_title}",
                f"状态：{'存在' if record.exists else '已删除'}",
                "",
            ]
        )
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output


def export_json(records: list[SessionRecord], output_path: Path | None = None) -> Path:
    output = output_path or DEFAULT_JSON_OUTPUT
    output.write_text(
        json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


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


def list_backups(limit: int = 8) -> list[Path]:
    if not BACKUP_DIR.exists():
        return []
    return sorted(
        [path for path in BACKUP_DIR.iterdir() if path.is_dir()],
        key=lambda p: p.name,
        reverse=True,
    )[:limit]


def load_recoverable_session_ids(limit: int = 8) -> set[str]:
    """扫描最近备份，找出理论上可恢复的会话 ID。

    判断标准是：备份里既有该会话的元数据，也有对应的 rollout 文件。
    """

    recoverable_ids: set[str] = set()
    for backup_dir in list_backups(limit):
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


def find_backup_for_session(session_id: str, limit: int = 8) -> Path | None:
    """找到包含指定会话的最近一份备份。

    当前恢复能力仍是整库恢复，这里只是帮 UI 找到“按这条记录触发恢复”时要用哪份备份。
    """

    clean_id = session_id.strip()
    if not clean_id:
        return None

    recoverable_ids = load_recoverable_session_ids(limit)
    if clean_id not in recoverable_ids:
        return None

    for backup_dir in list_backups(limit):
        file_map = _load_session_file_map(backup_dir)
        file_info = file_map.get(clean_id)
        if not file_info:
            continue
        backup_name = file_info.get("backup_name", "")
        if backup_name and (backup_dir / "sessions" / backup_name).exists():
            return backup_dir

    return None


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

    current_conn = sqlite3.connect(DB_PATH)
    current_conn.execute(
        f"insert or replace into threads ({column_list}) values ({placeholders})",
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
    """批量删除会话，并同步清理对应 rollout 文件。"""

    clean_ids = [session_id.strip() for session_id in session_ids if session_id.strip()]
    if not clean_ids:
        return "请先选择要删除的会话。"

    backup_dir = ensure_backup([HISTORY_PATH, SESSION_INDEX_PATH, DB_PATH])
    records = {item.id: item for item in load_sessions()}
    backup_session_rollouts(backup_dir, [record for session_id, record in records.items() if session_id in clean_ids])

    if HISTORY_PATH.exists():
        kept_lines = [
            line
            for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines()
            if not any(f'"session_id":"{session_id}"' in line for session_id in clean_ids)
        ]
        HISTORY_PATH.write_text("\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8")

    index_rows = [row for row in load_session_index() if str(row.get("id", "")) not in clean_ids]
    write_jsonl(SESSION_INDEX_PATH, index_rows)

    conn = sqlite3.connect(DB_PATH)
    conn.executemany("delete from threads where id = ?", [(session_id,) for session_id in clean_ids])
    conn.commit()
    conn.close()

    removed_files = 0
    for session_id in clean_ids:
        record = records.get(session_id)
        if record and record.rollout_path:
            rollout_path = Path(record.rollout_path)
            if rollout_path.exists():
                rollout_path.unlink()
                removed_files += 1

    return f"已删除 {len(clean_ids)} 条会话，清理 {removed_files} 个会话文件。备份已保存到 {backup_dir}"


def rename_session(session_id: str, new_name: str) -> str:
    """真实修改 Codex 中保存的会话标题。"""

    clean_name = new_name.strip()
    if not clean_name:
        return "新标题不能为空。"

    backup_dir = ensure_backup([SESSION_INDEX_PATH, DB_PATH])
    rows = load_session_index()
    found = False
    for row in rows:
        if str(row.get("id", "")) == session_id:
            row["thread_name"] = clean_name
            row["updated_at"] = dt.datetime.now(dt.UTC).isoformat()
            found = True
            break

    if not found:
        rows.append({"id": session_id, "thread_name": clean_name, "updated_at": dt.datetime.now(dt.UTC).isoformat()})

    write_jsonl(SESSION_INDEX_PATH, rows)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("update threads set title = ? where id = ?", (clean_name, session_id))
    conn.commit()
    conn.close()
    return f"已重命名会话 {session_id}。备份已保存到 {backup_dir}"
