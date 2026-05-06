"""页面 CSS 渲染入口。"""

from __future__ import annotations

from web.style_sections import render_sections


def render_styles(
    *,
    theme_vars: dict[str, str],
    is_apple: bool,
    is_cohere: bool,
    is_lamborghini: bool,
    surface_bg: str,
    panel_bg: str,
    body_background: str,
    font_stack: str,
    control_radius: str,
    hero_radius: str,
    card_radius: str,
    table_radius: str,
    surface_shadow: str,
    primary_button_bg: str,
    blur_css: str,
) -> str:
    """聚合各 CSS 分区，保持前端无构建依赖。"""

    ctx = {
        "theme_vars": theme_vars,
        "is_apple": is_apple,
        "is_cohere": is_cohere,
        "is_lamborghini": is_lamborghini,
        "surface_bg": surface_bg,
        "panel_bg": panel_bg,
        "body_background": body_background,
        "font_stack": font_stack,
        "control_radius": control_radius,
        "hero_radius": hero_radius,
        "card_radius": card_radius,
        "table_radius": table_radius,
        "surface_shadow": surface_shadow,
        "primary_button_bg": primary_button_bg,
        "blur_css": blur_css,
    }
    return f"  <style>{render_sections(ctx)}\n  </style>"
