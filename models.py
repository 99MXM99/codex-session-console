"""项目内共享的数据模型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SessionRecord:
    """单条会话在页面和导出时需要的聚合信息。"""

    id: str
    created_at: int
    created_at_text: str
    theme: str
    thread_name: str
    renamed_title: str
    rollout_path: str
    exists: bool


@dataclass
class ViewState:
    """页面当前的筛选、分页与主题状态。"""

    query: str = ""
    status: str = "existing"
    page: int = 1
    page_window: int = 0
    page_size: int = 10
    theme: str = "paper"
    message: str = ""
