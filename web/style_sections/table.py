"""table 样式分区。"""

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

    return f"""/* 工程与列表区域：左侧控制工程范围，右侧展示该范围内的会话。 */
    .workspace-grid {{
      display: grid;
      grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
      gap: 14px;
      align-items: stretch;
    }}
    .panel {{
      background: var(--panel-bg);
      border: 1px solid var(--line);
      border-radius: var(--card-radius);
      padding: 14px;
      {blur_css}
    }}
    .panel h2 {{ margin: 0 0 10px; font-size: 15px; }}
    .project-panel {{
      display: flex;
      flex-direction: column;
      align-self: stretch;
      min-height: 0;
      overflow: hidden;
      padding: 14px;
      box-shadow: var(--surface-shadow);
      background: var(--surface-bg);
    }}
    .project-current {{
      margin-top: 4px;
      color: var(--ink);
      font-size: 18px;
      font-weight: 650;
      line-height: 1.2;
      word-break: break-word;
    }}
    .project-list {{
      display: flex;
      flex: 1 1 auto;
      flex-direction: column;
      gap: 8px;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 4px 2px 2px 0;
    }}
    .project-link {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      min-height: 38px;
      padding: 9px 10px;
      border: 1px solid var(--line);
      border-radius: calc(var(--control-radius) + 2px);
      background: rgba(255,255,255,0.62);
      color: var(--ink);
      text-decoration: none;
      transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
    }}
    .project-link:hover {{
      transform: translateY(-1px);
      border-color: var(--accent);
    }}
    .project-link.active {{
      background: var(--primary-button-bg);
      border-color: var(--accent);
      color: #ffffff;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.10);
    }}
    .project-name {{
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 12px;
      font-weight: 650;
    }}
    .project-count {{
      flex: 0 0 auto;
      min-width: 24px;
      padding: 2px 7px;
      border-radius: 999px;
      background: rgba(0,0,0,0.06);
      color: var(--muted);
      font-size: 11px;
      text-align: center;
    }}
    .project-link.active .project-count {{
      background: rgba(255,255,255,0.22);
      color: #ffffff;
    }}
    .session-column {{
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .list-panel {{
      padding: 14px 14px 10px;
      box-shadow: var(--surface-shadow);
      background: var(--surface-bg);
    }}
    .list-panel-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .list-meta {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .meta-pill {{
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: {"rgba(28,28,32,0.92)" if is_lamborghini else "rgba(255,255,255,0.76)"};
      color: var(--muted);
      font-size: 11px;
      white-space: nowrap;
    }}
    table {{
      width: 100%;
      table-layout: fixed;
      border-collapse: collapse;
      margin-top: 14px;
      background: rgba(255,255,255,0.74);
      border: 1px solid var(--line);
      border-radius: calc(var(--table-radius) - 4px);
      overflow: visible;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
      {blur_css}
    }}
    col.select-width {{ width: 42px; }}
    col.id-width {{ width: 20%; }}
    col.time-width {{ width: 18%; }}
    col.title-width {{ width: 23%; }}
    col.theme-width {{ width: 23%; }}
    col.actions-width {{ width: 132px; }}
    th, td {{
      text-align: center;
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: middle;
      word-break: break-word;
      overflow: hidden;
    }}
    th {{
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    th.select-head, td.select-col {{ width: 42px; padding-left: 8px; padding-right: 8px; }}
    th.id-head, td.id-cell {{ width: 20%; }}
    th.time-head, td.time-cell {{ width: 18%; }}
    th.title-head, td.title-cell {{ width: 23%; }}
    th.theme-head, td.theme-cell {{ width: 23%; }}
    th.actions-head, td.actions {{ width: 132px; }}
    tbody tr:last-child td {{ border-bottom: 0; }}
    .id-cell, .actions, .theme-cell {{ text-align: center; }}
    .actions {{
      position: relative;
      overflow: visible;
      z-index: 30;
    }}
    tbody tr.row-menu-open,
    tbody tr:has(.row-action.open) {{
      position: relative;
      z-index: 25;
    }}
    .title-cell, .theme-cell {{
      font-size: 12px;
    }}
    .time-cell {{
      color: var(--muted);
      font-size: 11px;
      white-space: nowrap;
    }}

    /* 主题列：列表中只展示两行，完整首条用户对话继续通过 title 悬停查看。 */
    .theme-text {{
      display: -webkit-box;
      max-width: 22em;
      margin: 0 auto;
      overflow: hidden;
      line-height: 1.35;
      text-align: center;
      text-overflow: ellipsis;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
    }}

    /* ID 单元格：复制提示需要浮在表格行上方，所以这里允许溢出显示。 */
    .id-cell {{
      position: relative;
      overflow: visible;
      z-index: 2;
    }}
    .id-wrap {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      flex-wrap: nowrap;
      min-height: 20px;
    }}
    .status-dot {{
      width: 12px;
      height: 12px;
      border-radius: 999px;
      flex: 0 0 auto;
      box-shadow:
        inset 0 0 0 1px rgba(0,0,0,0.12),
        0 0 0 2px rgba(255,255,255,0.9);
    }}
    .id-cell code {{
      font-size: 12px;
      white-space: nowrap;
    }}
    .copy-button {{
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.92);
      color: var(--muted);
      cursor: pointer;
      font-size: 12px;
      padding: 0;
    }}
    .copy-button:hover {{
      color: var(--accent);
      border-color: var(--accent);
    }}
    .copy-button.copied {{
      color: #ffffff;
      border-color: var(--accent);
      background: var(--accent);
      transform: translateY(-1px);
      box-shadow: 0 8px 18px rgba(24, 99, 220, 0.18);
    }}
    .copy-button.copied::after {{
      content: "已复制";
      position: absolute;
      top: -30px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 12;
      white-space: nowrap;
      padding: 4px 8px;
      border-radius: 999px;
      background: rgba(20, 24, 31, 0.92);
      color: #ffffff;
      font-size: 10px;
      line-height: 1;
      letter-spacing: 0;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
      pointer-events: none;
    }}
    .row-check {{ width: 16px; height: 16px; }}
    .batch-delete {{ margin: 0; }}

    /* 行内操作：底部批量删除和单行标题按钮共享轻量布局。 */
    .inline-actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
    }}
    .action-form {{ display: inline-flex; margin: 0; }}
    .row-action {{
      position: relative;
      display: inline-flex;
      justify-content: center;
    }}
    .action-menu-button {{
      min-width: 42px;
      font-size: 15px;
      font-weight: 800;
      letter-spacing: 0.08em;
    }}
    .row-action-menu {{
      position: fixed;
      z-index: 500;
      display: none;
      min-width: 104px;
      padding: 6px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: var(--surface-bg);
      box-shadow: var(--surface-shadow);
      {blur_css}
    }}
    .row-action-menu.open {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .row-action-menu button {{
      width: 100%;
      padding: 8px 9px;
      border: 0;
      border-radius: 9px;
      background: transparent;
      color: var(--ink);
      cursor: pointer;
      font-size: 12px;
      text-align: left;
      white-space: nowrap;
    }}
    .row-action-menu button:hover {{
      background: rgba(30,90,82,0.08);
      color: var(--accent);
    }}
    .command-trigger {{
      font-size: 15px;
    }}

    """
