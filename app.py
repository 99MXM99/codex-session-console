"""命令行入口。

这里故意保持很薄，只负责参数解析和调度。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from server import run_server
from store import export_json, export_txt, load_sessions


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数。"""

    parser = argparse.ArgumentParser(description="Local Codex session console")
    subparsers = parser.add_subparsers(dest="command")

    export_parser = subparsers.add_parser("export", help="Export session list")
    export_parser.add_argument("format", choices=["txt", "json"])
    export_parser.add_argument("--output", help="Optional custom output path")

    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8876)
    parser.add_argument("--open", action="store_true", help="Open browser automatically")
    return parser


def main() -> None:
    """程序主入口。"""

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "export":
        sessions = load_sessions()
        output = Path(args.output) if args.output else None
        if args.format == "txt":
            print(export_txt(sessions, output))
            return
        print(export_json(sessions, output))
        return

    run_server(args.host, args.port, open_ui=args.open)


if __name__ == "__main__":
    main()
