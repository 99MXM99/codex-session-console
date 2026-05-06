"""base 样式分区。"""

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

    return f"""
    /* 基础变量：主题在 Python 侧计算后注入，CSS 只消费变量。 */
    :root {{
      --bg: {theme_vars['bg']};
      --panel: {theme_vars['panel']};
      --ink: {theme_vars['ink']};
      --muted: {theme_vars['muted']};
      --line: {theme_vars['line']};
      --accent: {theme_vars['accent']};
      --accent-2: {theme_vars['accent_2']};
      --danger: {theme_vars['danger']};
      --shadow: {"rgba(0, 0, 0, 0.38)" if is_lamborghini else "rgba(59, 41, 24, 0.08)"};
      --surface-bg: {surface_bg};
      --panel-bg: {panel_bg};
      --body-bg: {body_background};
      --font-stack: {font_stack};
      --control-radius: {control_radius};
      --hero-radius: {hero_radius};
      --card-radius: {card_radius};
      --table-radius: {table_radius};
      --surface-shadow: {surface_shadow};
      --primary-button-bg: {primary_button_bg};
    }}
    /* 页面基础：控制整页背景、主容器和基础文字。 */
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: var(--font-stack);
      color: var(--ink);
      background-color: var(--bg);
      position: relative;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      z-index: -1;
      background: var(--body-bg);
      background-repeat: no-repeat;
      background-size: cover;
      background-attachment: fixed;
    }}
    .wrap {{ max-width: 1240px; margin: 0 auto; padding: 24px 18px 40px; }}
    .page-stack {{ display: flex; flex-direction: column; gap: 18px; }}
    h1 {{ margin: 0; font-size: 38px; line-height: 1.02; letter-spacing: -0.04em; font-weight: 650; }}
    .sub {{ color: var(--muted); margin: 0; font-size: 13px; }}

    """
