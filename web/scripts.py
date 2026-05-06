"""页面脚本渲染。"""

from __future__ import annotations


def render_scripts(auto_refresh_ms: int) -> str:
    """渲染无构建依赖的页面交互脚本。"""

    return f"""  <script>
    const AUTO_REFRESH_MS = {auto_refresh_ms};
    let autoRefreshTimer = null;
    let activeActionButton = null;
    function appendSelectedSessionIds(form) {{
      form.querySelectorAll('input[name="session_ids"]').forEach((item) => item.remove());
      const checked = Array.from(document.querySelectorAll('.row-check:checked'));
      checked.forEach((item) => {{
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'session_ids';
        input.value = item.value;
        form.appendChild(input);
      }});
      return checked;
    }}
    function submitDeleteSelected(form) {{
      const checked = appendSelectedSessionIds(form);
      if (checked.length === 0) {{
        window.alert('请先选择要删除的会话');
        return false;
      }}
      if (!window.confirm('确认删除已选中的会话？')) {{
        return false;
      }}
      return true;
    }}
    function submitOpenSelected(form) {{
      const checked = appendSelectedSessionIds(form);
      if (checked.length === 0) {{
        window.alert('请先选择要开启的会话');
        return false;
      }}
      return true;
    }}
    function submitPurgeSelected(form) {{
      const checked = appendSelectedSessionIds(form);
      if (checked.length === 0) {{
        window.alert('请先选择要彻底删除的会话');
        return false;
      }}
      if (!window.confirm('确认彻底删除已选中的会话？这会同时清理当前 Codex 数据和所有备份中的这条记录。')) {{
        return false;
      }}
      return true;
    }}
    function toggleAll(checked) {{
      document.querySelectorAll('.row-check').forEach((item) => {{
        item.checked = checked;
      }});
    }}
    function showCopyFeedback(button) {{
      if (!button) return;
      const originalLabel = button.dataset.label || button.textContent;
      button.dataset.label = originalLabel;
      button.textContent = '✓';
      button.classList.add('copied');
      window.setTimeout(() => {{
        button.textContent = button.dataset.label || originalLabel;
        button.classList.remove('copied');
      }}, 1100);
    }}
    async function copySessionId(sessionId, button = null) {{
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
      showCopyFeedback(button);
    }}
    function openCommandMenu() {{
      document.getElementById('commandModal').classList.add('open');
      scheduleAutoRefresh();
    }}
    function closeCommandMenu(event) {{
      if (event && event.target && event.target !== event.currentTarget) return;
      document.getElementById('commandModal').classList.remove('open');
      scheduleAutoRefresh();
    }}
    function copyCommand(command) {{
      copySessionId(command);
    }}
    function closeAllRowActionMenus() {{
      document.querySelectorAll('.row-action.open').forEach((item) => item.classList.remove('open'));
      document.querySelectorAll('tr.row-menu-open').forEach((item) => item.classList.remove('row-menu-open'));
      const menu = document.getElementById('rowActionMenu');
      if (menu) {{
        menu.classList.remove('open');
        menu.style.left = '';
        menu.style.top = '';
      }}
      activeActionButton = null;
    }}
    function toggleRowActionMenu(button) {{
      if (!button) return;
      const wrapper = button.closest('.row-action');
      const wasOpen = wrapper && wrapper.classList.contains('open');
      closeAllRowActionMenus();
      if (wrapper && !wasOpen) {{
        wrapper.classList.add('open');
        activeActionButton = button;
        const row = wrapper.closest('tr');
        if (row) row.classList.add('row-menu-open');
        const menu = document.getElementById('rowActionMenu');
        if (menu) {{
          menu.classList.add('open');
          menu.style.visibility = 'hidden';
          const rect = button.getBoundingClientRect();
          const width = menu.offsetWidth || 112;
          const left = Math.max(8, Math.min(rect.right - width, window.innerWidth - width - 8));
          const top = Math.max(8, Math.min(rect.bottom + 6, window.innerHeight - menu.offsetHeight - 8));
          menu.style.left = `${{left}}px`;
          menu.style.top = `${{top}}px`;
          menu.style.visibility = 'visible';
        }}
      }}
      scheduleAutoRefresh();
    }}
    function openRenameDialogFromActiveAction() {{
      if (activeActionButton) openRenameDialogFromButton(activeActionButton);
    }}
    function openClassDialogFromActiveAction() {{
      if (activeActionButton) openClassDialogFromButton(activeActionButton);
    }}
    function openRenameDialogFromButton(button) {{
      if (!button) return;
      closeAllRowActionMenus();
      openRenameDialog(
        button.dataset.sessionId || '',
        button.dataset.currentTitle || '',
        button.dataset.query || '',
        button.dataset.project || '',
        button.dataset.status || 'existing',
        button.dataset.page || '1',
        button.dataset.window || '1',
        button.dataset.pageSize || '10',
        button.dataset.theme || 'paper'
      );
    }}
    function openRenameDialog(sessionId, currentTitle, query, project, status, page, windowValue, pageSize, theme) {{
      const nextTitle = window.prompt('改标题', currentTitle || '');
      if (nextTitle === null) return;
      const form = document.createElement('form');
      form.method = 'post';
      form.action = '/rename';
      const fields = {{
        session_id: sessionId,
        new_name: nextTitle,
        q: query,
        project: project,
        status: status,
        page: page,
        window: windowValue,
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
    function openClassDialogFromButton(button) {{
      if (!button) return;
      closeAllRowActionMenus();
      const modal = document.getElementById('classModal');
      document.getElementById('classSessionId').value = button.dataset.sessionId || '';
      document.getElementById('classQuery').value = button.dataset.query || '';
      document.getElementById('classProject').value = button.dataset.project || '';
      document.getElementById('classStatus').value = button.dataset.status || 'existing';
      document.getElementById('classPage').value = button.dataset.page || '1';
      document.getElementById('classWindow').value = button.dataset.window || '1';
      document.getElementById('classPageSize').value = button.dataset.pageSize || '10';
      document.getElementById('classTheme').value = button.dataset.theme || 'paper';
      const select = document.getElementById('classNameSelect');
      const input = document.getElementById('classNameInput');
      const keyInput = document.getElementById('classKeyInput');
      input.value = '';
      if (select) {{
        const currentClass = button.dataset.currentClass || '';
        const matched = Array.from(select.options).find((option) => option.dataset.name === currentClass || option.textContent === currentClass);
        select.value = matched ? matched.value : select.value;
        if (keyInput) keyInput.value = select.value;
      }}
      modal.classList.add('open');
      scheduleAutoRefresh();
    }}
    document.addEventListener('change', (event) => {{
      if (event.target && event.target.id === 'classNameSelect') {{
        const keyInput = document.getElementById('classKeyInput');
        if (keyInput) keyInput.value = event.target.value;
      }}
    }});
    document.addEventListener('submit', (event) => {{
      if (event.target && event.target.id === 'classForm') {{
        const select = document.getElementById('classNameSelect');
        const keyInput = document.getElementById('classKeyInput');
        if (select && keyInput && !document.getElementById('classNameInput').value.trim()) {{
          keyInput.value = select.value;
        }}
      }}
    }});
    function closeClassDialog(event) {{
      if (event && event.target && event.target !== event.currentTarget) return;
      document.getElementById('classModal').classList.remove('open');
      scheduleAutoRefresh();
    }}
    document.addEventListener('keydown', (event) => {{
      if (event.key === 'Escape') {{
        closeCommandMenu();
        closeClassDialog();
        closeAllRowActionMenus();
      }}
    }});
    document.addEventListener('click', (event) => {{
      if (!event.target.closest('.row-action') && !event.target.closest('#rowActionMenu')) {{
        closeAllRowActionMenus();
      }}
    }});
    function shouldPauseAutoRefresh() {{
      const modal = document.getElementById('commandModal');
      const classModal = document.getElementById('classModal');
      return document.visibilityState !== 'visible'
        || (modal && modal.classList.contains('open'))
        || (classModal && classModal.classList.contains('open'))
        || Boolean(document.querySelector('.row-action.open'));
    }}
    function scheduleAutoRefresh() {{
      if (autoRefreshTimer) {{
        window.clearTimeout(autoRefreshTimer);
      }}
      autoRefreshTimer = window.setTimeout(() => {{
        if (shouldPauseAutoRefresh()) {{
          scheduleAutoRefresh();
          return;
        }}
        window.location.reload();
      }}, AUTO_REFRESH_MS);
    }}
    document.addEventListener('visibilitychange', scheduleAutoRefresh);
    window.addEventListener('focus', scheduleAutoRefresh);
    scheduleAutoRefresh();
  </script>"""
