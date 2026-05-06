"""页头和搜索区域样式。"""

from __future__ import annotations


def render(ctx: dict[str, object]) -> str:
    """渲染页头与搜索模块 CSS。"""
    theme_vars = ctx["theme_vars"]
    is_apple = ctx["is_apple"]
    is_cohere = ctx["is_cohere"]
    is_lamborghini = ctx["is_lamborghini"]
    surface_bg = ctx["surface_bg"]
    panel_bg = ctx["panel_bg"]
    body_background = ctx["body_background"]
    font_stack = ctx["font_stack"]
    control_radius = ctx["control_radius"]
    hero_radius = ctx["hero_radius"]
    card_radius = ctx["card_radius"]
    table_radius = ctx["table_radius"]
    surface_shadow = ctx["surface_shadow"]
    primary_button_bg = ctx["primary_button_bg"]
    blur_css = ctx["blur_css"]



    return f"""/* 页头区域：标题、版本、主题切换和快捷命令入口。 */
    .site-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      flex-wrap: wrap;
    }}
    .hero-main {{ flex: 1; min-width: 280px; }}
    .hero-title-card {{
      display: inline-flex;
      flex-direction: column;
      gap: 10px;
      max-width: 760px;
    }}
    .title-line {{
      display: flex;
      align-items: baseline;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .version-chip {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: {"rgba(27,27,31,0.92)" if is_lamborghini else "rgba(255,255,255,0.86)"};
      color: var(--muted);
      font-size: 10px;
      letter-spacing: 0.04em;
    }}
    .hero-meta {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 12px;
    }}
    .hero-tools {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .tool-cluster {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .hero-controls {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-radius: calc(var(--card-radius) - 2px);
      background: {"linear-gradient(180deg, rgba(32,32,36,0.9) 0%, rgba(19,19,22,0.78) 100%)" if is_lamborghini else "rgba(255,255,255,0.58)"};
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
      {blur_css}
    }}
    .control-label {{
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}

    /* 搜索区域：只承载检索和导出入口，避免和列表操作混在一起。 */
    .search-panel {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: stretch;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: var(--card-radius);
      background: var(--panel-bg);
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
      {blur_css}
    }}
    .section-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }}
    .section-title {{
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .search-panel .toolbar {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: stretch; width: 100%; }}

    """
