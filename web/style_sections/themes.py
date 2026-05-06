"""themes 样式分区。"""

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

    return f"""/* 主题覆盖：只调整视觉表现，不改变 DOM 结构和核心交互。 */
    .theme-apple .hero-tools,
    .theme-apple .search-panel .toolbar,
    .theme-apple .tabs,
    .theme-apple .footer-row {{
      gap: 10px;
    }}
    .theme-apple .copy-button,
    .theme-apple .tab,
    .theme-apple .button,
    .theme-apple select,
    .theme-apple input[type="search"],
    .theme-apple input[type="text"] {{
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }}
    .theme-apple .page-link.active {{
      box-shadow: 0 8px 18px rgba(0, 113, 227, 0.22);
    }}
    .theme-apple .tab.active,
    .theme-apple .button.primary {{
      color: #ffffff;
    }}
    .theme-paper .tab.active,
    .theme-paper .button.primary,
    .theme-paper .page-link.active {{
      color: #fffdf8;
    }}
    .theme-cohere .hero-title-card {{
      position: relative;
      padding: 2px 0 0;
    }}
    .theme-cohere h1 {{
      font-weight: 480;
      letter-spacing: -0.02em;
    }}
    .theme-cohere .hero-title-card::before {{
      content: "";
      width: 68px;
      height: 6px;
      border-radius: 999px;
      background: linear-gradient(90deg, #1863dc 0%, #9b60aa 100%);
      margin-bottom: 10px;
    }}
    .theme-cohere .hero-controls,
    .theme-cohere .project-link,
    .theme-cohere .search-panel,
    .theme-cohere .list-panel,
    .theme-cohere table,
    .theme-cohere .command-dialog,
    .theme-cohere .command-item {{
      border-color: #d9d9dd;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
    }}
    .theme-cohere .hero-controls {{
      background-color: #ffffff;
      background-image: linear-gradient(180deg, #ffffff 0%, #fafafd 100%);
    }}
    .theme-cohere .search-panel,
    .theme-cohere .list-panel,
    .theme-cohere .command-item {{
      background-color: #fbfbfc;
    }}
    .theme-cohere .tab,
    .theme-cohere .project-link,
    .theme-cohere .button,
    .theme-cohere select,
    .theme-cohere input[type="search"],
    .theme-cohere input[type="text"],
    .theme-cohere .copy-button {{
      background-color: #ffffff;
      border-color: #d9d9dd;
      box-shadow: none;
    }}
    .theme-cohere .tab.active,
    .theme-cohere .project-link.active,
    .theme-cohere .button.primary,
    .theme-cohere .page-link.active {{
      color: #1863dc;
      -webkit-text-fill-color: #1863dc;
      background: rgba(24, 99, 220, 0.10);
      border-color: rgba(24, 99, 220, 0.22);
      box-shadow: 0 2px 5px rgba(24, 99, 220, 0.18);
    }}
    .theme-cohere select {{
      color: #1863dc;
      -webkit-text-fill-color: #1863dc;
    }}
    .theme-cohere select option {{
      color: #1863dc;
      background: #ffffff;
    }}
    .theme-cohere .meta-pill {{
      background: #ffffff;
      color: #5d5d69;
    }}
    .theme-cohere .section-title,
    .theme-cohere .control-label,
    .theme-cohere .hero-meta,
    .theme-cohere .sub,
    .theme-cohere .readonly-note,
    .theme-cohere th,
    .theme-cohere .page-ellipsis,
    .theme-cohere .copy-button {{
      color: #7a7a86;
    }}
    .theme-cohere .flash {{
      background: rgba(24, 99, 220, 0.06);
      border-color: rgba(24, 99, 220, 0.14);
      color: #1863dc;
    }}
    .theme-cohere .button.subtle {{
      background: rgba(24, 99, 220, 0.04);
      border-color: rgba(24, 99, 220, 0.10);
      color: #1863dc;
    }}
    .theme-cohere .button.danger {{
      background: linear-gradient(90deg, #1863dc 0%, #9b60aa 100%);
      border-color: rgba(24, 99, 220, 0.18);
      color: #ffffff;
      box-shadow: 0 3px 7px rgba(88, 92, 196, 0.20);
    }}
    .theme-lamborghini h1 {{
      text-transform: uppercase;
      letter-spacing: 0.03em;
      font-weight: 700;
    }}
    .theme-lamborghini .version-chip,
    .theme-lamborghini .meta-pill,
    .theme-lamborghini .hero-controls,
    .theme-lamborghini .search-panel,
    .theme-lamborghini .list-panel,
    .theme-lamborghini table {{
      border-color: rgba(246, 195, 0, 0.18);
    }}
    .theme-lamborghini .list-panel {{
      background: linear-gradient(180deg, rgba(25, 25, 29, 0.94) 0%, rgba(19, 19, 22, 0.88) 100%);
    }}
    .theme-lamborghini table {{
      background: rgba(31, 31, 36, 0.94);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
    }}
    .theme-lamborghini thead {{
      background: rgba(246, 195, 0, 0.08);
    }}
    .theme-lamborghini td {{
      color: #f6f1de;
    }}
    .theme-lamborghini .tab,
    .theme-lamborghini .project-link,
    .theme-lamborghini .button,
    .theme-lamborghini select,
    .theme-lamborghini input[type="search"],
    .theme-lamborghini input[type="text"],
    .theme-lamborghini .copy-button {{
      background-color: rgba(27, 27, 31, 0.94);
      color: var(--ink);
      border-color: rgba(246, 195, 0, 0.16);
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
    }}
    .theme-lamborghini .tab,
    .theme-lamborghini .project-link,
    .theme-lamborghini .button.subtle,
    .theme-lamborghini .copy-button {{
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.16);
    }}
    .theme-lamborghini .tab.active,
    .theme-lamborghini .project-link.active,
    .theme-lamborghini .button.primary,
    .theme-lamborghini .page-link.active {{
      color: #ffffff;
      border-color: #f6c300;
      box-shadow: 0 12px 26px rgba(246, 195, 0, 0.26);
      text-shadow: 0 1px 0 rgba(0, 0, 0, 0.18);
    }}
    .theme-lamborghini select {{
      color: #ffffff;
      -webkit-text-fill-color: #ffffff;
    }}
    .theme-lamborghini select option {{
      color: #ffffff;
      background: #1b1b1f;
    }}
    .theme-lamborghini .button.danger {{
      background: linear-gradient(180deg, #ff6a53 0%, #d94a38 100%);
      border-color: #ff7b67;
      color: #fff8f2;
      box-shadow: 0 14px 30px rgba(217, 74, 56, 0.34);
    }}
    .theme-lamborghini .button.subtle {{
      background: rgba(246, 195, 0, 0.06);
      border-color: rgba(246, 195, 0, 0.14);
      color: #d7c78a;
    }}
    .theme-lamborghini .flash {{
      background: rgba(246, 195, 0, 0.10);
      border-color: rgba(246, 195, 0, 0.22);
      color: #ffe58f;
    }}
    .theme-lamborghini .help-button:hover,
    .theme-lamborghini .help-button:focus-visible {{
      box-shadow: 0 12px 28px rgba(246, 195, 0, 0.24);
    }}
    .theme-lamborghini .readonly-note,
    .theme-lamborghini .control-label,
    .theme-lamborghini .sub,
    .theme-lamborghini .hero-meta,
    .theme-lamborghini th,
    .theme-lamborghini .page-ellipsis,
    .theme-lamborghini .copy-button {{
      color: var(--muted);
    }}
    .theme-lamborghini .id-cell code,
    .theme-lamborghini .command-dialog-title strong,
    .theme-lamborghini .command-text code {{
      color: #fff2b5;
    }}
    .theme-lamborghini .command-item {{
      background: rgba(27, 27, 31, 0.92);
      border-color: rgba(246, 195, 0, 0.18);
    }}

    """
