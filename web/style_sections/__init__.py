"""页面样式分区聚合。"""

from __future__ import annotations

from . import base, controls, layout, overlays, responsive, table, themes

SECTIONS = (
    base,
    layout,
    controls,
    table,
    overlays,
    themes,
    responsive,
)


def render_sections(ctx: dict[str, object]) -> str:
    """按 DOM 区域顺序拼接 CSS，避免样式补丁散落。"""
    return "".join(section.render(ctx) for section in SECTIONS)
