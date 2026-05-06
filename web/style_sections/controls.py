"""controls 样式分区。"""

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

    return f"""/* 公共控件：按钮、标签页、图标按钮和基础表单控件复用这里。 */
    .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 0; }}
    .tab, .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      text-decoration: none;
      min-height: 36px;
      padding: 8px 12px;
      border-radius: var(--control-radius);
      border: 1px solid var(--line);
      color: var(--ink);
      background: rgba(255,255,255,0.9);
      cursor: pointer;
      font-size: 11px;
      line-height: 1.2;
      white-space: nowrap;
      transition: transform 140ms ease, background 140ms ease, border-color 140ms ease;
    }}
    .tab:hover, .button:hover {{ transform: translateY(-1px); }}
    .tab.active, .button.primary {{
      background: var(--primary-button-bg);
      border-color: var(--accent);
      color: #ffffff;
      text-shadow: 0 1px 0 rgba(0, 0, 0, 0.08);
    }}
    .button.danger {{
      background: var(--danger);
      border-color: var(--danger);
      color: #fffaf2;
      font-weight: 700;
      box-shadow: 0 10px 24px rgba(138, 59, 46, 0.20);
    }}
    .button.subtle {{
      background: rgba(30,90,82,0.05);
      border-color: rgba(30,90,82,0.12);
      color: var(--accent-2);
    }}
    .button.small {{ padding: 8px 11px; min-height: 36px; }}
    .icon-button {{
      width: 40px;
      min-width: 40px;
      padding: 0;
      font-size: 16px;
      line-height: 1;
    }}
    .help-button {{
      position: relative;
      transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
    }}
    .help-button::after {{
      content: attr(data-tip);
      position: absolute;
      top: calc(100% + 10px);
      right: 0;
      opacity: 0;
      transform: translateY(-4px);
      pointer-events: none;
      white-space: nowrap;
      padding: 8px 10px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: var(--surface-bg);
      color: var(--muted);
      font-size: 11px;
      box-shadow: 0 10px 24px var(--shadow);
      transition: opacity 160ms ease, transform 160ms ease;
      {blur_css}
    }}
    .help-button:hover,
    .help-button:focus-visible {{
      transform: translateY(-1px) scale(1.03);
      border-color: var(--accent);
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
    }}
    .help-button:hover::after,
    .help-button:focus-visible::after {{
      opacity: 1;
      transform: translateY(0);
    }}
    select,
    input[type="search"], input[type="text"] {{
      min-width: 220px;
      min-height: 36px;
      padding: 8px 11px;
      border-radius: var(--control-radius);
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.92);
      font-size: 12px;
      color: var(--ink);
    }}
    select option {{
      color: #1f1d1a;
      background: #fffdf8;
    }}
    select {{
      appearance: none;
      -webkit-appearance: none;
      padding-right: 34px;
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position:
        calc(100% - 14px) calc(50% - 1px),
        calc(100% - 10px) calc(50% - 1px);
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
    }}
    .toolbar input[type="search"] {{ flex: 1; min-width: 280px; }}

    /* 反馈信息：写操作失败或成功后的页面级提示。 */
    .flash {{
      margin-top: 14px;
      padding: 10px 12px;
      background: rgba(40,93,83,0.1);
      border: 1px solid rgba(40,93,83,0.24);
      border-radius: 12px;
      color: var(--accent-2);
      font-size: 12px;
    }}

    """
