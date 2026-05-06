"""responsive 样式分区。"""

from __future__ import annotations


def render(ctx: dict[str, object]) -> str:
    """渲染本分区 CSS。"""
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

    return f"""/* 响应式：小屏只调整布局密度，不改变功能位置。 */
    @media (max-width: 760px) {{
      .wrap {{ padding: 14px 10px 28px; }}
      h1 {{ font-size: 31px; }}
      .actions {{ width: auto; }}
      .workspace-grid {{ grid-template-columns: 1fr; }}
      .project-panel {{
        max-height: none;
        overflow: visible;
      }}
      .project-list {{
        max-height: none;
        overflow: visible;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      }}
      .hero-controls {{ width: 100%; justify-content: space-between; }}
      .tool-cluster {{ width: 100%; }}
      .search-panel .toolbar {{ flex-direction: column; }}
      .list-panel-head {{ align-items: flex-start; }}
      .command-item {{
        align-items: flex-start;
        flex-direction: column;
      }}
    }}"""
