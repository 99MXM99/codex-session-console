"""会话自定义分类管理。

这里保存的是管理器自己的分类映射，不修改 Codex 记录里的真实 cwd。
"""

from __future__ import annotations

import json
from pathlib import Path

from config import CLASS_MAP_PATH


def _normalize_class_name(name: str) -> str:
    """规整用户输入的分类名，避免空白和过长名称影响界面。"""

    return " ".join(name.strip().split())[:80]


def load_session_classes() -> dict[str, str]:
    """读取会话 ID 到分类 key 的映射，兼容旧版本保存的分类名。"""

    if not CLASS_MAP_PATH.exists():
        return {}
    try:
        data = json.loads(CLASS_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    result: dict[str, str] = {}
    for session_id, class_name in data.items():
        clean_id = str(session_id).strip()
        raw_value = str(class_name).strip()
        if raw_value.startswith(("cwd:", "class:")):
            clean_value = raw_value
        else:
            clean_name = _normalize_class_name(raw_value)
            clean_value = custom_class_key(clean_name) if clean_name else ""
        if clean_id and clean_value:
            result[clean_id] = clean_value
    return result


def save_session_classes(mapping: dict[str, str]) -> None:
    """写入分类映射，父目录不存在时自动创建。"""

    CLASS_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLASS_MAP_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def set_session_class(session_id: str, class_name: str) -> str:
    """给单条会话设置管理器内的自定义分类。"""

    clean_id = session_id.strip()
    clean_name = _normalize_class_name(class_name)
    if not clean_id:
        return "会话 ID 不能为空。"
    if not clean_name:
        return "分类名不能为空。"
    mapping = load_session_classes()
    mapping[clean_id] = custom_class_key(clean_name)
    save_session_classes(mapping)
    return f"已将会话 {clean_id} 移动到分类：{clean_name}"


def set_session_class_value(session_id: str, class_key: str, class_name: str) -> tuple[str, str]:
    """按已有分类 key 或新分类名设置分类，并返回新的筛选 key。"""

    clean_key = class_key.strip()
    clean_name = _normalize_class_name(class_name)
    if clean_key.startswith("cwd:"):
        target_name = default_class_name(clean_key.removeprefix("cwd:"))
        clean_id = session_id.strip()
        if not clean_id:
            return "", "会话 ID 不能为空。"
        mapping = load_session_classes()
        mapping[clean_id] = clean_key
        save_session_classes(mapping)
        message = f"已将会话 {clean_id} 移动到分类：{target_name}"
        return clean_key, message
    if clean_key.startswith("class:"):
        target_name = clean_key.removeprefix("class:")
        clean_id = session_id.strip()
        if not clean_id:
            return "", "会话 ID 不能为空。"
        mapping = load_session_classes()
        mapping[clean_id] = custom_class_key(target_name)
        save_session_classes(mapping)
        message = f"已将会话 {clean_id} 移动到分类：{target_name}"
        return custom_class_key(target_name), message
    message = set_session_class(session_id, clean_name)
    return custom_class_key(clean_name), message


def default_class_name(project_path: str) -> str:
    """从真实 cwd 推导默认分类名。"""

    cleaned = project_path.strip()
    if not cleaned:
        return "未识别工程"
    if cleaned == str(Path.home()):
        return "Default Class"
    return Path(cleaned).name or cleaned


def default_class_key(project_path: str) -> str:
    """为真实 cwd 生成稳定筛选 key，避免和自定义分类名冲突。"""

    return f"cwd:{project_path.strip()}"


def custom_class_key(class_name: str) -> str:
    """为自定义分类生成稳定筛选 key。"""

    return f"class:{_normalize_class_name(class_name)}"
