"""弹窗和分页区域样式。"""

from __future__ import annotations


def render(ctx: dict[str, object]) -> str:
    """渲染命令弹窗、分页和批量操作 CSS。"""
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



    return f"""/* 快捷命令弹窗：只负责命令展示与复制，不影响主表格布局。 */
    .command-modal {{
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
      z-index: 60;
      background: rgba(10, 12, 16, 0.38);
    }}
    .command-modal.open {{
      display: flex;
    }}
    .command-dialog {{
      width: min(560px, 100%);
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: calc(var(--card-radius) + 2px);
      background: var(--surface-bg);
      box-shadow: var(--surface-shadow);
      {blur_css}
    }}
    .command-dialog-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }}
    .command-dialog-title {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .command-dialog-title strong {{
      font-size: 15px;
      line-height: 1.2;
    }}
    .command-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .command-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--panel-bg);
    }}
    .command-copy {{
      flex: 0 0 auto;
    }}
    .command-text {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }}
    .command-text code {{
      font-size: 12px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .command-note {{
      color: var(--muted);
      font-size: 11px;
      line-height: 1.4;
    }}
    .class-dialog {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .class-field {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      color: var(--muted);
      font-size: 11px;
    }}
    .class-field select,
    .class-field input {{
      width: 100%;
      min-width: 0;
    }}
    .dialog-actions {{
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 4px;
    }}

    /* 分页区域：页码窗口、上一页下一页和批量操作放在同一模块。 */
    .footer-panel {{ margin-top: 0; }}
    .footer-row {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .footer-meta {{
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .pager-inline {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .page-size-form {{ display: flex; gap: 8px; align-items: center; }}
    .page-size-form select {{ min-width: 78px; min-height: 34px; padding: 6px 10px; }}
    .pagination {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }}
    .inline-pagination {{ margin-top: 0; gap: 6px; }}
    .page-nav, .window-nav {{ gap: 6px; }}
    .page-link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 24px;
      height: 24px;
      border-radius: 7px;
      text-decoration: none;
      border: 0;
      background: transparent;
      color: var(--ink);
      font-size: 11px;
    }}
    .jump-link {{
      min-width: 58px;
      padding: 0 10px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.56);
    }}
    .page-link.disabled {{
      opacity: 0.38;
      pointer-events: none;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.28);
    }}
    .page-link.active {{ background: var(--accent); color: #fffaf2; }}
    .page-ellipsis {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 18px;
      height: 24px;
      color: var(--muted);
      font-size: 11px;
    }}
    .readonly-note {{ color: var(--muted); font-size: 11px; line-height: 1.5; padding-top: 2px; }}

    """
