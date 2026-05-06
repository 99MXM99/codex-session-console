"""SQLite threads 表修复和写入辅助函数。"""

from __future__ import annotations

import sqlite3
from collections import OrderedDict
from pathlib import Path

from config import DB_PATH

def _delete_thread_rows_by_scan(conn: sqlite3.Connection, session_ids: set[str]) -> int:
    rows = conn.execute("select rowid, id from threads").fetchall()
    rowids_to_delete = [rowid for rowid, session_id in rows if str(session_id).strip() in session_ids]
    if rowids_to_delete:
        conn.executemany("delete from threads where rowid = ?", [(rowid,) for rowid in rowids_to_delete])
        conn.commit()
    return len(rowids_to_delete)


def _rebuild_threads_table(path: Path) -> None:
    """重建 threads 表，修复坏索引和重复 id。"""

    conn = sqlite3.connect(path)
    try:
        table_sql = conn.execute("select sql from sqlite_master where type='table' and name='threads'").fetchone()
        if not table_sql or not table_sql[0]:
            return

        aux_sql = conn.execute(
            """
            select type, name, sql
            from sqlite_master
            where tbl_name='threads' and type in ('index', 'trigger') and sql is not null
            order by type, name
            """
        ).fetchall()
        columns = [row[1] for row in conn.execute("pragma table_info(threads)").fetchall()]
        selected_columns = ", ".join(columns)
        rows = conn.execute(f"select rowid, {selected_columns} from threads order by rowid desc").fetchall()

        deduped_rows: OrderedDict[str, tuple[Any, ...]] = OrderedDict()
        for row in rows:
            data = row[1:]
            session_id = str(data[0]).strip()
            if session_id not in deduped_rows:
                deduped_rows[session_id] = data

        conn.execute(table_sql[0].replace("threads", "threads_repaired", 1))
        placeholders = ", ".join(["?"] * len(columns))
        conn.executemany(
            f"insert into threads_repaired ({selected_columns}) values ({placeholders})",
            list(deduped_rows.values()),
        )
        conn.execute("drop table threads")
        conn.execute("alter table threads_repaired rename to threads")
        for _, _, sql in aux_sql:
            conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


def _remove_session_from_db(path: Path, session_ids: set[str]) -> None:
    if not path.exists() or not session_ids:
        return
    try:
        conn = sqlite3.connect(path)
        try:
            _delete_thread_rows_by_scan(conn, session_ids)
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        _rebuild_threads_table(path)
        conn = sqlite3.connect(path)
        try:
            _delete_thread_rows_by_scan(conn, session_ids)
        finally:
            conn.close()


def _remove_single_session_from_current_db(session_id: str) -> None:
    """按全表扫描删除当前库里的单条会话，绕开坏索引导致的精确匹配失效。"""

    _remove_session_from_db(DB_PATH, {session_id})


def _update_thread_title_in_db(path: Path, session_id: str, new_title: str) -> int:
    """按全表扫描更新标题，避免坏索引导致按 id 精确匹配失败。"""

    if not path.exists():
        return 0
    try:
        conn = sqlite3.connect(path)
        try:
            rows = conn.execute("select rowid, id from threads").fetchall()
            rowids = [rowid for rowid, raw_id in rows if str(raw_id).strip() == session_id]
            if rowids:
                conn.executemany("update threads set title = ? where rowid = ?", [(new_title, rowid) for rowid in rowids])
                conn.commit()
            return len(rowids)
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        _rebuild_threads_table(path)
        conn = sqlite3.connect(path)
        try:
            rows = conn.execute("select rowid, id from threads").fetchall()
            rowids = [rowid for rowid, raw_id in rows if str(raw_id).strip() == session_id]
            if rowids:
                conn.executemany("update threads set title = ? where rowid = ?", [(new_title, rowid) for rowid in rowids])
                conn.commit()
            return len(rowids)
        finally:
            conn.close()

