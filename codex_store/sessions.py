"""会话读取、筛选、分页和导出。"""

from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
from dataclasses import asdict
from math import ceil
from pathlib import Path
from typing import Any

from config import DB_PATH, DEFAULT_JSON_OUTPUT, DEFAULT_TXT_OUTPUT, SESSION_INDEX_PATH, TZ
from models import SessionRecord
from codex_store.classes import custom_class_key, default_class_key, default_class_name, load_session_classes
from codex_store.text import format_ts

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
    class_overrides = load_session_classes()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        select rowid, id, created_at, updated_at, first_user_message, title, cwd, rollout_path
        from threads
        where source = 'cli'
        order by created_at desc, rowid desc
        """
    ).fetchall()
    conn.close()
    default_keys_by_name = {
        default_class_name(str(row["cwd"] or "").strip()).lower(): default_class_key(str(row["cwd"] or "").strip())
        for row in rows
    }

    sessions: list[SessionRecord] = []
    seen_ids: set[str] = set()
    for row in rows:
        session_id = str(row["id"])
        if session_id in seen_ids:
            continue
        seen_ids.add(session_id)
        rollout_path = str(row["rollout_path"] or "")
        exists = bool(rollout_path and os.path.exists(rollout_path))
        first_user_raw = str(row["first_user_message"] or "").strip()
        codex_title = str(row["title"] or "").strip()
        project_path = str(row["cwd"] or "").strip()
        custom_class_value = class_overrides.get(session_id, "")
        if custom_class_value.startswith("cwd:"):
            class_key = custom_class_value
            class_name = default_class_name(custom_class_value.removeprefix("cwd:"))
        elif custom_class_value.startswith("class:"):
            class_name = custom_class_value.removeprefix("class:")
            class_key = default_keys_by_name.get(class_name.lower(), custom_class_value)
            if class_key.startswith("cwd:"):
                class_name = default_class_name(class_key.removeprefix("cwd:"))
        else:
            class_name = custom_class_value or default_class_name(project_path)
            class_key = custom_class_key(custom_class_value) if custom_class_value else default_class_key(project_path)
        thread_name = names.get(session_id, "").strip()
        renamed_title = thread_name or "未设置标题"
        sessions.append(
            SessionRecord(
                id=session_id,
                created_at=int(row["created_at"]),
                created_at_text=format_ts(int(row["created_at"])),
                updated_at_text=format_ts(int(row["updated_at"])),
                codex_title=codex_title,
                first_user_message=first_user_raw,
                thread_name=thread_name,
                renamed_title=renamed_title,
                class_key=class_key,
                class_name=class_name,
                project_path=project_path,
                rollout_path=rollout_path,
                exists=exists,
            )
        )
    return sessions


def filter_by_project(records: list[SessionRecord], project: str) -> list[SessionRecord]:
    """按管理器分类筛选，兼容旧 URL 中直接传 cwd 的情况。"""

    chosen = project.strip()
    if not chosen:
        return records
    return [record for record in records if record.class_key == chosen or record.project_path == chosen]


def filter_sessions(records: list[SessionRecord], query: str) -> list[SessionRecord]:
    q = query.strip().lower()
    if not q:
        return records
    return [
        record
        for record in records
        if q in record.id.lower()
        or q in record.codex_title.lower()
        or q in record.first_user_message.lower()
        or q in record.thread_name.lower()
        or q in record.renamed_title.lower()
        or q in record.class_name.lower()
        or q in record.project_path.lower()
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
                f"分类：{record.class_name}",
                f"工程目录：{record.project_path or '未识别工程'}",
                f"Codex 标题：{record.codex_title or '未设置标题'}",
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
