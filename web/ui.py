"""页面渲染层。

保持零前端构建依赖，直接返回完整 HTML。
"""

from __future__ import annotations

import datetime as dt
import html
from collections import Counter
from urllib.parse import urlencode

from models import SessionRecord, ViewState
from codex_store.store import load_recoverable_session_ids, paginate_records, resolve_theme
from web.scripts import render_scripts
from web.styles import render_styles

UI_VERSION = "v2026.05.07-7"
AUTO_REFRESH_MS = 60_000
PROJECT_NAME_DISPLAY_LIMIT = 24


def shorten_project_name(name: str) -> str:
    """限制左侧分类名展示长度，避免长英文路径挤压布局。"""

    clean_name = name.strip()
    if len(clean_name) <= PROJECT_NAME_DISPLAY_LIMIT:
        return clean_name
    return f"{clean_name[:PROJECT_NAME_DISPLAY_LIMIT]}..."


def build_view_query(state: ViewState, message: str | None = None) -> str:
    """把页面状态重新编码成 URL 查询参数。"""

    return urlencode(
        {
            "q": state.query,
            "project": state.project,
            "status": state.status,
            "page": state.page,
            "window": state.page_window,
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
    max_window_start = max(1, total_pages - 4)
    requested_window_start = state.page_window if state.page_window > 0 else current_page
    window_start = max(1, min(requested_window_start, max_window_start))
    if current_page < window_start or current_page > window_start + 4:
        window_start = max(1, min(current_page, max_window_start))
    window_end = min(total_pages, window_start + 4)
    recoverable_ids = load_recoverable_session_ids()
    rows: list[str] = []

    def view_href(**overrides: object) -> str:
        """保留当前视图状态，只覆盖本次链接需要改变的字段。"""

        params = {
            "status": state.status,
            "q": state.query,
            "project": state.project,
            "page": current_page,
            "window": window_start,
            "page_size": state.page_size,
            "theme": theme_name,
        }
        params.update(overrides)
        return "/?" + urlencode(params)

    for record in page_records:
        is_recoverable = (not record.exists) and (record.id in recoverable_ids)
        state_label = "可继续对话" if record.exists else ("已删除（可恢复）" if is_recoverable else "已删除（不可恢复）")
        dot_color = "#1f9d62" if record.exists else ("#d79a00" if is_recoverable else "#d63f32")
        short_id = f"{record.id[:6]}...{record.id[-4:]}" if len(record.id) > 14 else record.id
        row_selectable = (state.status == "existing" and record.exists) or (state.status == "deleted" and not record.exists)
        select_cell = f'<input class="row-check" type="checkbox" name="session_ids" value="{html.escape(record.id)}">' if row_selectable else ""
        if record.exists:
            actions = f"""
                <div class="row-action">
                  <button
                    class="button small action-menu-button"
                    type="button"
                    title="更多操作"
                    aria-label="更多操作"
                    data-session-id="{html.escape(record.id)}"
                    data-current-title="{html.escape(record.thread_name)}"
                    data-current-class="{html.escape(record.class_name)}"
                    data-query="{html.escape(state.query)}"
                    data-project="{html.escape(state.project)}"
                    data-status="{html.escape(state.status)}"
                    data-page="{current_page}"
                    data-window="{window_start}"
                    data-page-size="{state.page_size}"
                    data-theme="{html.escape(theme_name)}"
                    onclick="toggleRowActionMenu(this)"
                  >···</button>
                </div>
            """
        elif is_recoverable:
            actions = f"""
                <form method="post" action="/restore_session" onsubmit="return confirm('将恢复包含这条会话的整份备份，确认继续？');">
                  <input type="hidden" name="session_id" value="{html.escape(record.id)}">
                  <input type="hidden" name="q" value="{html.escape(state.query)}">
                  <input type="hidden" name="project" value="{html.escape(state.project)}">
                  <input type="hidden" name="status" value="{html.escape(state.status)}">
                  <input type="hidden" name="page" value="{current_page}">
                  <input type="hidden" name="window" value="{window_start}">
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
                  <button class="copy-button" type="button" title="复制完整 ID" aria-label="复制完整 ID" onclick="copySessionId('{html.escape(record.id)}', this)">⧉</button>
                </span>
              </td>
              <td class="time-cell" title="最后打开：{html.escape(record.updated_at_text)}">{html.escape(record.created_at_text)}</td>
              <td class="title-cell">{html.escape(record.renamed_title)}</td>
              <td class="theme-cell" title="{html.escape(record.first_user_message)}"><span class="theme-text">{html.escape(record.codex_title or '未设置标题')}</span></td>
              <td class="actions">{actions}</td>
            </tr>
            """
        )

    def tab(label: str, value: str) -> str:
        cls = "tab active" if state.status == value else "tab"
        href = view_href(status=value, page=1, window=0)
        return f'<a class="{cls}" href="{href}">{label}</a>'

    message_html = f'<div class="flash">{html.escape(state.message)}</div>' if state.message else ""
    scoped_records = [item for item in all_records if not state.project or item.class_key == state.project or item.project_path == state.project]
    existing_total = sum(1 for item in scoped_records if item.exists)
    deleted_total = sum(1 for item in scoped_records if not item.exists)
    existing_records = [record for record in all_records if record.exists]
    visible_class_keys = {record.class_key for record in existing_records}
    class_names = {record.class_key: record.class_name for record in all_records}
    project_counts = Counter(record.class_key for record in all_records if record.class_key in visible_class_keys)
    class_options = "".join(
        f'<option value="{html.escape(class_key)}" data-name="{html.escape(class_names[class_key])}">{html.escape(class_names[class_key])}</option>'
        for class_key in sorted(visible_class_keys, key=lambda key: class_names.get(key, "").lower())
    )
    project_links = [
        f"""
          <a class="project-link {'active' if not state.project else ''}" href="{view_href(project='', status='existing', page=1, window=0)}">
            <span class="project-name">全部会话</span>
            <span class="project-count">{len(all_records)}</span>
          </a>
        """
    ]
    for class_key, count in sorted(project_counts.items(), key=lambda item: (-item[1], class_names.get(item[0], "").lower())):
        class_name = class_names.get(class_key, "未识别工程")
        project_links.append(
            f"""
          <a class="project-link {'active' if state.project == class_key else ''}" title="{html.escape(class_name)}" href="{view_href(project=class_key, status='existing', page=1, window=0)}">
            <span class="project-name">{html.escape(shorten_project_name(class_name))}</span>
            <span class="project-count">{count}</span>
          </a>
            """
        )
    active_project_name = class_names.get(state.project, state.project.removeprefix("class:").removeprefix("cwd:")) if state.project else "全部会话"
    active_project_display = shorten_project_name(active_project_name)

    page_links: list[str] = []
    window_nav_links: list[str] = []
    page_nav_links: list[str] = []
    visible_pages = list(range(window_start, window_end + 1)) or [1]
    previous_window_link = ""
    next_window_link = ""
    if window_start > 1:
        previous_window_start = max(1, window_start - 5)
        previous_window_href = view_href(window=previous_window_start)
        previous_window_link = f'<a class="page-link nav-link" href="{previous_window_href}" aria-label="Previous Page Numbers">‹</a>'
    else:
        previous_window_link = '<span class="page-link nav-link disabled" aria-hidden="true">‹</span>'
    for page_no in visible_pages:
        href = view_href(page=page_no)
        cls = "page-link active" if page_no == current_page else "page-link"
        page_links.append(f'<a class="{cls}" href="{href}">{page_no}</a>')
    if window_end < total_pages:
        next_window_start = min(max_window_start, window_start + 5)
        next_window_href = view_href(window=next_window_start)
        next_window_link = f'<a class="page-link nav-link" href="{next_window_href}" aria-label="Next Page Numbers">›</a>'
    else:
        next_window_link = '<span class="page-link nav-link disabled" aria-hidden="true">›</span>'
    if current_page > 1:
        prev_href = view_href(page=current_page - 1)
        page_nav_links.append(f'<a class="page-link jump-link" href="{prev_href}">Prev</a>')
    else:
        page_nav_links.append('<span class="page-link jump-link disabled" aria-hidden="true">Prev</span>')
    if current_page < total_pages:
        next_href = view_href(page=current_page + 1)
        page_nav_links.append(f'<a class="page-link jump-link" href="{next_href}">Next</a>')
    else:
        page_nav_links.append('<span class="page-link jump-link disabled" aria-hidden="true">Next</span>')

    footer_actions = ""
    if state.status == "existing":
        footer_actions = f"""
          <div class="batch-delete inline-actions">
            <button class="button subtle" type="button" onclick="toggleAll(true)">全选</button>
            <button class="button subtle" type="button" onclick="toggleAll(false)">清空</button>
            <form method="post" action="/open_selected" class="action-form" onsubmit="return submitOpenSelected(this);">
              <input type="hidden" name="q" value="{html.escape(state.query)}">
              <input type="hidden" name="project" value="{html.escape(state.project)}">
              <input type="hidden" name="status" value="{html.escape(state.status)}">
              <input type="hidden" name="page" value="{current_page}">
              <input type="hidden" name="window" value="{window_start}">
              <input type="hidden" name="page_size" value="{state.page_size}">
              <input type="hidden" name="theme" value="{html.escape(theme_name)}">
              <button class="button primary" type="submit">开启已选会话</button>
            </form>
            <form method="post" action="/delete_selected" class="action-form" onsubmit="return submitDeleteSelected(this);">
              <input type="hidden" name="q" value="{html.escape(state.query)}">
              <input type="hidden" name="project" value="{html.escape(state.project)}">
              <input type="hidden" name="status" value="{html.escape(state.status)}">
              <input type="hidden" name="page" value="{current_page}">
              <input type="hidden" name="window" value="{window_start}">
              <input type="hidden" name="page_size" value="{state.page_size}">
              <input type="hidden" name="theme" value="{html.escape(theme_name)}">
              <button class="button danger" type="submit">删除已选</button>
            </form>
          </div>
        """
    elif state.status == "deleted":
        footer_actions = f"""
          <form method="post" action="/purge_selected" class="batch-delete inline-actions" onsubmit="return submitPurgeSelected(this);">
            <input type="hidden" name="q" value="{html.escape(state.query)}">
            <input type="hidden" name="project" value="{html.escape(state.project)}">
            <input type="hidden" name="status" value="{html.escape(state.status)}">
            <input type="hidden" name="page" value="{current_page}">
            <input type="hidden" name="window" value="{window_start}">
            <input type="hidden" name="page_size" value="{state.page_size}">
            <input type="hidden" name="theme" value="{html.escape(theme_name)}">
            <button class="button subtle" type="button" onclick="toggleAll(true)">全选</button>
            <button class="button subtle" type="button" onclick="toggleAll(false)">清空</button>
            <button class="button danger" type="submit">彻底删除已选</button>
          </form>
        """

    pagination = f"""
        <section class="panel footer-panel">
        <div class="footer-row">
          <div class="footer-meta">
            <div class="pager-inline">
              <div class="readonly-note">第 {current_page} / {total_pages} 页</div>
              <div class="pagination inline-pagination page-nav">{''.join(page_nav_links)}</div>
              <div class="pagination inline-pagination window-nav">{previous_window_link}</div>
              <div class="pagination inline-pagination">{''.join(page_links)}</div>
              <div class="pagination inline-pagination window-nav">{next_window_link}</div>
              <div class="readonly-note">共 {len(records)} 条</div>
            </div>
            <form method="get" action="/" class="page-size-form">
              <input type="hidden" name="status" value="{html.escape(state.status)}">
              <input type="hidden" name="project" value="{html.escape(state.project)}">
              <input type="hidden" name="q" value="{html.escape(state.query)}">
              <input type="hidden" name="window" value="{window_start}">
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
{render_styles(theme_vars=theme_vars, is_apple=is_apple, is_cohere=is_cohere, is_lamborghini=is_lamborghini, surface_bg=surface_bg, panel_bg=panel_bg, body_background=body_background, font_stack=font_stack, control_radius=control_radius, hero_radius=hero_radius, card_radius=card_radius, table_radius=table_radius, surface_shadow=surface_shadow, primary_button_bg=primary_button_bg, blur_css=blur_css)}
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
              <input type="hidden" name="project" value="{html.escape(state.project)}">
              <input type="hidden" name="page" value="{current_page}">
              <input type="hidden" name="window" value="{window_start}">
              <input type="hidden" name="page_size" value="{state.page_size}">
              <span class="control-label">Style</span>
              <select name="theme" aria-label="选择主题" onchange="this.form.submit()">
                {theme_options}
              </select>
              <a class="button icon-button" title="刷新" aria-label="刷新" href="{view_href()}">&#8635;</a>
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
          <input type="hidden" name="project" value="{html.escape(state.project)}">
          <input type="hidden" name="page" value="{current_page}">
          <input type="hidden" name="window" value="{window_start}">
          <input type="hidden" name="page_size" value="{state.page_size}">
          <input type="hidden" name="theme" value="{html.escape(theme_name)}">
          <input type="search" name="q" placeholder="搜索会话 ID、Codex 标题、自定义标题或工程路径" value="{html.escape(state.query)}">
          <button class="button primary" type="submit">搜索</button>
          <a class="button" href="/export.txt">导出 TXT</a>
          <a class="button" href="/export.json">导出 JSON</a>
        </form>
      </section>
      <section class="workspace-grid">
        <aside class="panel project-panel">
          <div class="section-head">
            <div>
              <div class="section-title">Projects/Class</div>
              <div class="project-current" title="{html.escape(active_project_name)}">{html.escape(active_project_display)}</div>
            </div>
          </div>
          <div class="project-list">
            {''.join(project_links)}
          </div>
        </aside>
        <div class="session-column">
          <section class="panel list-panel">
            <div class="list-panel-head">
              <div class="tabs">
                {tab("可继续", "existing")}
                {tab("已删除", "deleted")}
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
                <col class="title-width">
                <col class="theme-width">
                <col class="actions-width">
              </colgroup>
              <thead>
                <tr>
                  <th class="select-head"></th>
                  <th class="id-head">ID</th>
                  <th class="time-head">时间</th>
                  <th class="title-head">标题</th>
                  <th class="theme-head">主题</th>
                  <th class="actions-head">操作</th>
                </tr>
              </thead>
              <tbody>
                {''.join(rows)}
              </tbody>
            </table>
          </section>
          {pagination}
        </div>
      </section>
    </div>
  </div>
  <div class="row-action-menu global-row-action-menu" id="rowActionMenu">
    <button type="button" onclick="openRenameDialogFromActiveAction()">改标题</button>
    <button type="button" onclick="openClassDialogFromActiveAction()">改分类</button>
  </div>
  <div class="command-modal" id="classModal" onclick="closeClassDialog(event)">
    <form class="command-dialog class-dialog" id="classForm" method="post" action="/set_class" onclick="event.stopPropagation()">
      <div class="command-dialog-head">
        <div class="command-dialog-title">
          <strong>修改分类</strong>
          <div class="command-note">这里只修改管理器里的分类，不会改变 Codex 会话真实目录。</div>
        </div>
        <button class="button icon-button" type="button" title="关闭" aria-label="关闭" onclick="closeClassDialog()">×</button>
      </div>
      <input type="hidden" name="session_id" id="classSessionId">
      <input type="hidden" name="q" id="classQuery">
      <input type="hidden" name="project" id="classProject">
      <input type="hidden" name="status" id="classStatus">
      <input type="hidden" name="page" id="classPage">
      <input type="hidden" name="window" id="classWindow">
      <input type="hidden" name="page_size" id="classPageSize">
      <input type="hidden" name="theme" id="classTheme">
      <label class="class-field">
        <span>选择已有分类</span>
        <select name="class_name" id="classNameSelect">
          {class_options}
        </select>
        <input type="hidden" name="class_key" id="classKeyInput">
      </label>
      <label class="class-field">
        <span>或添加自定义分类</span>
        <input type="text" name="new_class_name" id="classNameInput" placeholder="输入新的分类名">
      </label>
      <div class="dialog-actions">
        <button class="button subtle" type="button" onclick="closeClassDialog()">取消</button>
        <button class="button primary" type="submit">保存分类</button>
      </div>
    </form>
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
{render_scripts(AUTO_REFRESH_MS)}
</body>
</html>
"""
