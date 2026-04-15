"""页面渲染层。

保持零前端构建依赖，直接返回完整 HTML。
"""

from __future__ import annotations

import datetime as dt
import html
from urllib.parse import urlencode

from models import SessionRecord, ViewState
from store import load_recoverable_session_ids, paginate_records, resolve_theme

UI_VERSION = "v2026.04.15-2"


def build_view_query(state: ViewState, message: str | None = None) -> str:
    """把页面状态重新编码成 URL 查询参数。"""

    return urlencode(
        {
            "q": state.query,
            "status": state.status,
            "page": state.page,
            "page_size": state.page_size,
            "theme": state.theme,
            "msg": state.message if message is None else message,
        }
    )


def render_html(records: list[SessionRecord], all_records: list[SessionRecord], state: ViewState) -> str:
    """根据当前视图状态渲染完整页面。"""

    theme_name, theme_vars = resolve_theme(state.theme)
    is_apple = theme_name == "apple"
    is_cohere = theme_name == "cohere"
    is_lamborghini = theme_name == "lamborghini"
    page_records, current_page, total_pages = paginate_records(records, state.page, state.page_size)
    recoverable_ids = load_recoverable_session_ids()
    rows: list[str] = []

    for record in page_records:
        is_recoverable = (not record.exists) and (record.id in recoverable_ids)
        state_label = "可继续对话" if record.exists else ("已删除（可恢复）" if is_recoverable else "已删除（不可恢复）")
        dot_color = "#1f9d62" if record.exists else ("#d79a00" if is_recoverable else "#d63f32")
        short_id = f"{record.id[:8]}...{record.id[-6:]}" if len(record.id) > 18 else record.id
        select_cell = (
            f'<input class="row-check" type="checkbox" name="session_ids" value="{html.escape(record.id)}">'
            if record.exists and state.status == "existing"
            else ""
        )
        if record.exists:
            actions = f"""
                <details class="action-menu">
                  <summary class="action-trigger" aria-label="更多操作" title="更多操作">⋯</summary>
                  <div class="action-panel">
                    <button
                      class="button small menu-item"
                      type="button"
                      onclick="openRenameDialog('{html.escape(record.id)}', '{html.escape(record.thread_name)}', '{html.escape(state.query)}', '{html.escape(state.status)}', '{current_page}', '{state.page_size}', '{html.escape(theme_name)}')"
                    >设置标题</button>
                  </div>
                </details>
            """
        elif is_recoverable:
            actions = f"""
                <form method="post" action="/restore_session" onsubmit="return confirm('将恢复包含这条会话的整份备份，确认继续？');">
                  <input type="hidden" name="session_id" value="{html.escape(record.id)}">
                  <input type="hidden" name="q" value="{html.escape(state.query)}">
                  <input type="hidden" name="status" value="{html.escape(state.status)}">
                  <input type="hidden" name="page" value="{current_page}">
                  <input type="hidden" name="page_size" value="{state.page_size}">
                  <input type="hidden" name="theme" value="{html.escape(theme_name)}">
                  <button class="button small subtle" type="submit">恢复</button>
                </form>
            """
        else:
            actions = '<div class="readonly-note">只读</div>'

        rows.append(
            f"""
            <tr>
              <td class="select-col">{select_cell}</td>
              <td class="id-cell">
                <span class="id-wrap">
                  <span class="status-dot" style="background:{dot_color};" title="{state_label}" aria-label="{state_label}"></span>
                  <code>{html.escape(short_id)}</code>
                  <button class="copy-button" type="button" title="复制完整 ID" aria-label="复制完整 ID" onclick="copySessionId('{html.escape(record.id)}')">⧉</button>
                </span>
              </td>
              <td>{html.escape(record.created_at_text)}</td>
              <td>{html.escape(record.theme)}</td>
              <td>{html.escape(record.renamed_title)}</td>
              <td class="actions">{actions}</td>
            </tr>
            """
        )

    def tab(label: str, value: str) -> str:
        cls = "tab active" if state.status == value else "tab"
        href = "/?" + urlencode({"status": value, "q": state.query, "page_size": state.page_size, "theme": theme_name})
        return f'<a class="{cls}" href="{href}">{label}</a>'

    message_html = f'<div class="flash">{html.escape(state.message)}</div>' if state.message else ""
    existing_total = sum(1 for item in all_records if item.exists)
    deleted_total = sum(1 for item in all_records if not item.exists)

    page_links = []
    visible_pages = list(range(current_page, min(total_pages, current_page + 4) + 1))
    if not visible_pages:
        visible_pages = [1]
    for page_no in visible_pages:
        href = "/?" + urlencode({"status": state.status, "q": state.query, "page": page_no, "page_size": state.page_size, "theme": theme_name})
        cls = "page-link active" if page_no == current_page else "page-link"
        page_links.append(f'<a class="{cls}" href="{href}">{page_no}</a>')
    if visible_pages[-1] < total_pages:
        page_links.append('<span class="page-ellipsis">...</span>')

    footer_actions = ""
    if state.status == "existing":
        footer_actions = f"""
          <form method="post" action="/delete_selected" class="batch-delete inline-actions" onsubmit="return submitDeleteSelected(this);">
            <input type="hidden" name="q" value="{html.escape(state.query)}">
            <input type="hidden" name="status" value="{html.escape(state.status)}">
            <input type="hidden" name="page" value="{current_page}">
            <input type="hidden" name="page_size" value="{state.page_size}">
            <input type="hidden" name="theme" value="{html.escape(theme_name)}">
            <button class="button subtle" type="button" onclick="toggleAll(true)">全选</button>
            <button class="button subtle" type="button" onclick="toggleAll(false)">清空</button>
            <button class="button danger" type="submit">删除已选</button>
          </form>
        """

    pagination = f"""
        <section class="panel footer-panel">
        <div class="footer-row">
          <div class="footer-meta">
            <div class="pager-inline">
              <div class="readonly-note">第 {current_page} / {total_pages} 页</div>
              <div class="pagination inline-pagination">{''.join(page_links)}</div>
              <div class="readonly-note">共 {len(records)} 条</div>
            </div>
            <form method="get" action="/" class="page-size-form">
              <input type="hidden" name="status" value="{html.escape(state.status)}">
              <input type="hidden" name="q" value="{html.escape(state.query)}">
              <input type="hidden" name="theme" value="{html.escape(theme_name)}">
              <label class="readonly-note" for="page_size">每页显示</label>
              <select name="page_size" id="page_size" onchange="this.form.submit()">
                {''.join(f'<option value="{size}" {"selected" if size == state.page_size else ""}>{size}</option>' for size in (10, 20, 30, 50))}
              </select>
            </form>
          </div>
          {footer_actions}
        </div>
      </section>
    """
    theme_options = "".join(
        f'<option value="{key}" {"selected" if key == theme_name else ""}>{label}</option>'
        for key, label in (("apple", "Apple"), ("paper", "Paper"), ("cohere", "Cohere"), ("lamborghini", "Lamborghini"))
    )
    build_stamp = dt.datetime.now().strftime("%H:%M:%S")
    font_stack = (
        '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif'
        if is_apple
        else (
            '"Avenir Next", "Inter", "Helvetica Neue", Arial, sans-serif'
            if is_cohere
            else ('"Oswald", "Arial Narrow", "Helvetica Neue", Arial, sans-serif' if is_lamborghini else '"Iowan Old Style", "Palatino Linotype", serif')
        )
    )
    body_background = (
        "radial-gradient(circle at 18% 0%, rgba(41,151,255,0.18), transparent 28%), "
        "radial-gradient(circle at 100% 0%, rgba(255,255,255,0.9), transparent 24%), "
        "linear-gradient(180deg, #f5f5f7 0%, #e9edf4 48%, #eef2f7 100%)"
        if is_apple
        else (
            "linear-gradient(180deg, #fbfbfc 0%, #ffffff 42%, #f6f6f9 100%), "
            "radial-gradient(circle at 18% 0%, rgba(155,96,170,0.08), transparent 22%), "
            "radial-gradient(circle at 100% 0%, rgba(24,99,220,0.08), transparent 26%)"
            if is_cohere
            else (
            "radial-gradient(circle at 14% 0%, rgba(246,195,0,0.22), transparent 24%), "
            "radial-gradient(circle at 86% 8%, rgba(255,223,102,0.12), transparent 20%), "
            "linear-gradient(135deg, #080809 0%, #111215 36%, #1a160d 100%)"
            if is_lamborghini
            else "radial-gradient(circle at top left, rgba(154,77,42,0.12), transparent 30%), linear-gradient(180deg, #efe4d3 0%, var(--bg) 42%)"
            )
        )
    )
    surface_bg = (
        "rgba(255,255,255,0.72)" if is_apple
        else ("rgba(255,255,255,0.96)" if is_cohere else ("rgba(24,24,28,0.86)" if is_lamborghini else "rgba(255,251,245,0.94)"))
    )
    panel_bg = (
        "rgba(255,255,255,0.66)" if is_apple
        else ("rgba(250,250,250,0.94)" if is_cohere else ("rgba(20,20,24,0.78)" if is_lamborghini else "rgba(255,251,245,0.72)"))
    )
    surface_shadow = (
        "0 24px 60px rgba(15, 23, 42, 0.10)" if is_apple
        else ("0 8px 24px rgba(0, 0, 0, 0.04)" if is_cohere else ("0 24px 72px rgba(0, 0, 0, 0.44)" if is_lamborghini else "0 12px 34px var(--shadow)"))
    )
    control_radius = "999px" if is_apple else ("14px" if is_cohere else ("10px" if is_lamborghini else "12px"))
    hero_radius = "30px" if is_apple else ("22px" if is_cohere else ("18px" if is_lamborghini else "22px"))
    card_radius = "22px" if is_apple else ("18px" if is_cohere else ("14px" if is_lamborghini else "16px"))
    table_radius = "24px" if is_apple else ("18px" if is_cohere else ("16px" if is_lamborghini else "18px"))
    blur_css = (
        "backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);"
        if is_apple
        else ('backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);' if is_lamborghini else "")
    )
    primary_button_bg = (
        "linear-gradient(180deg, #2d8cff 0%, #0071e3 100%)"
        if is_apple
        else ("linear-gradient(180deg, #2a76ef 0%, #1863dc 100%)" if is_cohere else ("linear-gradient(180deg, #ffd84d 0%, #f6c300 100%)" if is_lamborghini else "var(--accent)"))
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Session Console {UI_VERSION}</title>
  <style>
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
        calc(100% - 16px) calc(50% - 1px),
        calc(100% - 11px) calc(50% - 1px);
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
    }}
    .toolbar input[type="search"] {{ flex: 1; min-width: 280px; }}
    .flash {{
      margin-top: 14px;
      padding: 10px 12px;
      background: rgba(40,93,83,0.1);
      border: 1px solid rgba(40,93,83,0.24);
      border-radius: 12px;
      color: var(--accent-2);
      font-size: 12px;
    }}
    .panel {{
      background: var(--panel-bg);
      border: 1px solid var(--line);
      border-radius: var(--card-radius);
      padding: 14px;
      {blur_css}
    }}
    .panel h2 {{ margin: 0 0 10px; font-size: 15px; }}
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
      border-collapse: collapse;
      margin-top: 14px;
      background: rgba(255,255,255,0.74);
      border: 1px solid var(--line);
      border-radius: calc(var(--table-radius) - 4px);
      overflow: hidden;
      display: block;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
      {blur_css}
    }}
    thead, tbody, tr {{ display: table; width: 100%; table-layout: fixed; }}
    col.select-width {{ width: 42px; }}
    col.id-width {{ width: 19%; }}
    col.time-width {{ width: 19%; }}
    col.theme-width {{ width: 26%; }}
    col.title-width {{ width: 20%; }}
    col.actions-width {{ width: 132px; }}
    th, td {{
      text-align: center;
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: middle;
      word-break: break-word;
    }}
    th {{
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    tbody tr:last-child td {{ border-bottom: 0; }}
    .id-cell, .actions {{ text-align: center; }}
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
    .select-col {{ width: 42px; }}
    .actions {{ width: 132px; }}
    .row-check {{ width: 16px; height: 16px; }}
    .batch-delete {{ margin: 0; }}
    .inline-actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
    }}
    .action-menu {{
      position: relative;
      display: inline-block;
    }}
    .action-menu summary {{ list-style: none; }}
    .action-menu summary::-webkit-details-marker {{ display: none; }}
    .action-trigger {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255,255,255,0.92);
      color: var(--muted);
      cursor: pointer;
      font-size: 16px;
      line-height: 1;
    }}
    .action-trigger:hover {{
      color: var(--accent);
      border-color: var(--accent);
    }}
    .action-panel {{
      position: absolute;
      top: calc(100% + 8px);
      right: 0;
      z-index: 20;
      padding: 8px;
      min-width: 110px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,0.94);
      box-shadow: 0 8px 24px var(--shadow);
      {blur_css}
    }}
    .menu-item {{ width: 100%; }}
    .command-trigger {{
      font-size: 15px;
    }}
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
    .theme-apple .hero-tools,
    .theme-apple .search-panel .toolbar,
    .theme-apple .tabs,
    .theme-apple .footer-row {{
      gap: 10px;
    }}
    .theme-apple .copy-button,
    .theme-apple .action-trigger,
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
    .theme-cohere .hero-title-card::before {{
      content: "";
      width: 68px;
      height: 6px;
      border-radius: 999px;
      background: linear-gradient(90deg, #1863dc 0%, #9b60aa 100%);
      margin-bottom: 10px;
    }}
    .theme-cohere .hero-controls,
    .theme-cohere .search-panel,
    .theme-cohere .list-panel,
    .theme-cohere table,
    .theme-cohere .action-panel,
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
    .theme-cohere .button,
    .theme-cohere select,
    .theme-cohere input[type="search"],
    .theme-cohere input[type="text"],
    .theme-cohere .copy-button,
    .theme-cohere .action-trigger {{
      background-color: #ffffff;
      border-color: #d9d9dd;
      box-shadow: none;
    }}
    .theme-cohere .tab.active,
    .theme-cohere .button.primary,
    .theme-cohere .page-link.active {{
      color: #1863dc;
      -webkit-text-fill-color: #1863dc;
      background: rgba(24, 99, 220, 0.10);
      border-color: rgba(24, 99, 220, 0.22);
      box-shadow: 0 10px 20px rgba(24, 99, 220, 0.18);
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
      box-shadow: 0 12px 24px rgba(88, 92, 196, 0.20);
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
    .theme-lamborghini table,
    .theme-lamborghini .action-panel {{
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
    .theme-lamborghini .button,
    .theme-lamborghini select,
    .theme-lamborghini input[type="search"],
    .theme-lamborghini input[type="text"],
    .theme-lamborghini .copy-button,
    .theme-lamborghini .action-trigger {{
      background-color: rgba(27, 27, 31, 0.94);
      color: var(--ink);
      border-color: rgba(246, 195, 0, 0.16);
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
    }}
    .theme-lamborghini .tab,
    .theme-lamborghini .button.subtle,
    .theme-lamborghini .copy-button,
    .theme-lamborghini .action-trigger {{
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.16);
    }}
    .theme-lamborghini .tab.active,
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
    @media (max-width: 760px) {{
      .wrap {{ padding: 14px 10px 28px; }}
      h1 {{ font-size: 31px; }}
      .actions {{ width: auto; }}
      .hero-controls {{ width: 100%; justify-content: space-between; }}
      .tool-cluster {{ width: 100%; }}
      .search-panel .toolbar {{ flex-direction: column; }}
      .list-panel-head {{ align-items: flex-start; }}
      .command-item {{
        align-items: flex-start;
        flex-direction: column;
      }}
    }}
  </style>
</head>
<body class="theme-{theme_name}">
  <div class="wrap">
    <div class="page-stack">
      <header class="site-head">
        <div class="hero-main">
          <div class="hero-title-card">
            <div class="title-line">
              <h1>Codex Session Console</h1>
              <span class="version-chip">{UI_VERSION}</span>
            </div>
            <p class="sub">本地 Codex 会话管理界面。支持查看、筛选、真实重命名、真实删除，并自动备份底层记录。</p>
            <div class="hero-meta">
              <span>当前构建：{build_stamp}</span>
              <span>本地会话管理台</span>
            </div>
          </div>
        </div>
        <div class="hero-tools">
          <div class="tool-cluster">
            <button class="button icon-button command-trigger help-button" type="button" title="快捷命令" aria-label="快捷命令" data-tip="打开 Codex 快捷命令菜单" onclick="openCommandMenu()">⌘</button>
            <form class="hero-controls" method="get" action="/">
              <input type="hidden" name="status" value="{html.escape(state.status)}">
              <input type="hidden" name="q" value="{html.escape(state.query)}">
              <input type="hidden" name="page_size" value="{state.page_size}">
              <span class="control-label">Style</span>
              <select name="theme" aria-label="选择主题" onchange="this.form.submit()">
                {theme_options}
              </select>
              <a class="button icon-button" title="刷新" aria-label="刷新" href="/?{urlencode({'status': state.status, 'theme': theme_name, 'page_size': state.page_size, 'q': state.query})}">&#8635;</a>
            </form>
          </div>
        </div>
      </header>
      <section class="search-panel">
        <div class="section-head">
          <div class="section-title">Search</div>
        </div>
        <form class="toolbar" method="get" action="/">
          <input type="hidden" name="status" value="{html.escape(state.status)}">
          <input type="hidden" name="page_size" value="{state.page_size}">
          <input type="hidden" name="theme" value="{html.escape(theme_name)}">
          <input type="search" name="q" placeholder="搜索会话 ID、主题或标题" value="{html.escape(state.query)}">
          <button class="button primary" type="submit">搜索</button>
          <a class="button" href="/export.txt">导出 TXT</a>
          <a class="button" href="/export.json">导出 JSON</a>
        </form>
      </section>
      <section class="panel list-panel">
        <div class="list-panel-head">
          <div class="tabs">
            {tab("当前存在", "existing")}
            {tab("已删除", "deleted")}
            {tab("会话", "all")}
          </div>
          <div class="list-meta">
            <span class="meta-pill">当前视图 {len(records)} 条</span>
            <span class="meta-pill">现存 {existing_total}</span>
            <span class="meta-pill">已删除 {deleted_total}</span>
          </div>
        </div>
        {message_html}
        <table>
          <colgroup>
            <col class="select-width">
            <col class="id-width">
            <col class="time-width">
            <col class="theme-width">
            <col class="title-width">
            <col class="actions-width">
          </colgroup>
          <thead>
            <tr>
              <th></th>
              <th>ID</th>
              <th>时间</th>
              <th>主题</th>
              <th>标题</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </section>
      {pagination}
    </div>
  </div>
  <div class="command-modal" id="commandModal" onclick="closeCommandMenu(event)">
    <div class="command-dialog" role="dialog" aria-modal="true" aria-labelledby="commandMenuTitle" onclick="event.stopPropagation()">
      <div class="command-dialog-head">
        <div class="command-dialog-title">
          <strong id="commandMenuTitle">Codex 快捷命令</strong>
          <div class="command-note">点右侧按钮可直接复制命令，适合恢复会话、启动管理器或导出记录。</div>
        </div>
        <button class="button icon-button" type="button" title="关闭" aria-label="关闭" onclick="closeCommandMenu()">×</button>
      </div>
      <div class="command-list">
        <div class="command-item">
          <div class="command-text">
            <code>cdx resume</code>
            <div class="command-note">打开可恢复会话列表，自行选择继续的会话。</div>
          </div>
          <button class="button subtle small command-copy" type="button" onclick="copyCommand('cdx resume')">复制</button>
        </div>
        <div class="command-item">
          <div class="command-text">
            <code>cdx resume &lt;session_id&gt;</code>
            <div class="command-note">按会话 ID 直接恢复，适合从当前列表里复制后粘贴使用。</div>
          </div>
          <button class="button subtle small command-copy" type="button" onclick="copyCommand('cdx resume <session_id>')">复制</button>
        </div>
        <div class="command-item">
          <div class="command-text">
            <code>python3 app.py --open</code>
            <div class="command-note">在项目目录内直接启动当前管理器并打开页面。</div>
          </div>
          <button class="button subtle small command-copy" type="button" onclick="copyCommand('python3 app.py --open')">复制</button>
        </div>
        <div class="command-item">
          <div class="command-text">
            <code>python3 app.py export txt</code>
            <div class="command-note">导出文本格式的会话记录清单。</div>
          </div>
          <button class="button subtle small command-copy" type="button" onclick="copyCommand('python3 app.py export txt')">复制</button>
        </div>
        <div class="command-item">
          <div class="command-text">
            <code>python3 app.py export json</code>
            <div class="command-note">导出 JSON 格式的会话记录，便于后续处理。</div>
          </div>
          <button class="button subtle small command-copy" type="button" onclick="copyCommand('python3 app.py export json')">复制</button>
        </div>
      </div>
    </div>
  </div>
  <script>
    function submitDeleteSelected(form) {{
      form.querySelectorAll('input[name="session_ids"]').forEach((item) => item.remove());
      const checked = Array.from(document.querySelectorAll('.row-check:checked'));
      if (checked.length === 0) {{
        window.alert('请先选择要删除的会话');
        return false;
      }}
      if (!window.confirm('确认删除已选中的会话？')) {{
        return false;
      }}
      checked.forEach((item) => {{
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'session_ids';
        input.value = item.value;
        form.appendChild(input);
      }});
      return true;
    }}
    function toggleAll(checked) {{
      document.querySelectorAll('.row-check').forEach((item) => {{
        item.checked = checked;
      }});
    }}
    async function copySessionId(sessionId) {{
      try {{
        await navigator.clipboard.writeText(sessionId);
      }} catch (error) {{
        const textArea = document.createElement('textarea');
        textArea.value = sessionId;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }}
    }}
    function openCommandMenu() {{
      document.getElementById('commandModal').classList.add('open');
    }}
    function closeCommandMenu(event) {{
      if (event && event.target && event.target !== event.currentTarget) return;
      document.getElementById('commandModal').classList.remove('open');
    }}
    function copyCommand(command) {{
      copySessionId(command);
    }}
    function openRenameDialog(sessionId, currentTitle, query, status, page, pageSize, theme) {{
      const nextTitle = window.prompt('设置标题', currentTitle || '');
      if (nextTitle === null) return;
      const form = document.createElement('form');
      form.method = 'post';
      form.action = '/rename';
      const fields = {{
        session_id: sessionId,
        new_name: nextTitle,
        q: query,
        status: status,
        page: page,
        page_size: pageSize,
        theme: theme
      }};
      Object.entries(fields).forEach(([key, value]) => {{
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
      }});
      document.body.appendChild(form);
      form.submit();
    }}
    document.addEventListener('keydown', (event) => {{
      if (event.key === 'Escape') {{
        closeCommandMenu();
      }}
    }});
  </script>
</body>
</html>
"""
