"""HTTP 服务层。"""

from __future__ import annotations

import subprocess
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from config import DEFAULT_JSON_OUTPUT, DEFAULT_TXT_OUTPUT
from models import ViewState
from store import delete_sessions, export_json, export_txt, filter_by_status, filter_sessions, hard_delete_sessions, load_sessions, rename_session, restore_session
from ui import build_view_query, render_html


def parse_view_state(mapping: dict[str, list[str]]) -> ViewState:
    """从 query string 或表单参数恢复页面状态。"""

    def first(name: str, default: str) -> str:
        return mapping.get(name, [default])[0] or default

    def safe_int(name: str, default: int) -> int:
        try:
            return int(first(name, str(default)))
        except (TypeError, ValueError):
            return default

    status = first("status", "existing")
    if status not in {"existing", "deleted", "all"}:
        status = "existing"

    return ViewState(
        query=first("q", ""),
        status=status,
        page=safe_int("page", 1),
        page_window=safe_int("window", 0),
        page_size=safe_int("page_size", 10),
        theme=first("theme", "paper"),
        message=first("msg", ""),
    )


class AppHandler(BaseHTTPRequestHandler):
    """标准库 HTTP 处理器。"""

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        sessions = load_sessions()

        if parsed.path == "/export.txt":
            output = export_txt(sessions, DEFAULT_TXT_OUTPUT)
            self._send(200, output.read_text(encoding="utf-8"), "text/plain; charset=utf-8")
            return

        if parsed.path == "/export.json":
            output = export_json(sessions, DEFAULT_JSON_OUTPUT)
            self._send(200, output.read_text(encoding="utf-8"), "application/json; charset=utf-8")
            return

        state = parse_view_state(parse_qs(parsed.query))
        visible = filter_by_status(filter_sessions(sessions, state.query), state.status)
        self._send(200, render_html(visible, sessions, state), "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(body)
        state = parse_view_state(params)

        if self.path == "/delete_selected":
            message = self._run_action(lambda: delete_sessions(params.get("session_ids", [])))
            self._redirect(state, message)
            return

        if self.path == "/purge_selected":
            message = self._run_action(lambda: hard_delete_sessions(params.get("session_ids", [])))
            self._redirect(state, message)
            return

        if self.path == "/rename":
            session_id = params.get("session_id", [""])[0]
            new_name = params.get("new_name", [""])[0]
            message = self._run_action(lambda: rename_session(session_id, new_name))
            self._redirect(state, message)
            return

        if self.path == "/restore_session":
            session_id = params.get("session_id", [""])[0]
            message = self._run_action(lambda: restore_session(session_id))
            self._redirect(state, message)
            return

        self.send_error(404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _redirect(self, state: ViewState, message: str) -> None:
        state.message = message
        target = "/?" + build_view_query(state)
        self.send_response(303)
        self.send_header("Location", target)
        self.end_headers()

    def _send(self, status: int, body: str, content_type: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)

    def _run_action(self, action: Callable[[], str]) -> str:
        """执行写操作，并把常见写入错误转成可读消息。"""

        try:
            return str(action())
        except PermissionError as exc:
            print(traceback.format_exc(), flush=True)
            return (
                "写入 Codex 本地数据失败：权限不足。"
                f"目标文件：{exc.filename or '未知'}。"
                "请重新从桌面应用或启动器打开，而不是使用当前无写权限的实例。"
            )
        except OSError as exc:
            print(traceback.format_exc(), flush=True)
            return f"写入 Codex 本地数据失败：{exc}"
        except Exception as exc:
            print(traceback.format_exc(), flush=True)
            return f"操作失败：{exc}"


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    """允许快速重启，减少本地端口释放的等待时间。"""

    allow_reuse_address = True
    daemon_threads = True


def open_browser(url: str) -> None:
    """在 macOS 上尝试自动打开浏览器。"""

    try:
        subprocess.Popen(["open", url])
    except Exception:
        pass


def run_server(host: str, port: int, open_ui: bool = False) -> None:
    """启动本地 HTTP 服务。"""

    server = ReusableThreadingHTTPServer((host, port), AppHandler)
    url = f"http://{host}:{port}"
    print(f"Codex Session Console running at {url}", flush=True)
    if open_ui:
        open_browser(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
