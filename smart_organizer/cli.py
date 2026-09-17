"""Command-line interface."""

import argparse
import logging
from pathlib import Path

from .organizer import organize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="smart-organizer", description="Organize files by type.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    command = subcommands.add_parser("organize", help="Organize files directly inside a folder")
    command.add_argument("folder", type=Path, help="Folder to organize")
    command.add_argument("--dry-run", action="store_true", help="Preview without changing files")
    command.add_argument("--report", type=Path, metavar="PATH", help="Save a JSON report at PATH")
    web = subcommands.add_parser("web", help="Start the local web interface")
    web.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    web.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "web":
        try:
            import uvicorn
            from .web.routes import app
        except ImportError:
            parser.exit(1, "Error: Web dependencies missing. Install with: python -m pip install -e '.[web]'\n")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0
    if args.dry_run and args.report:
        parser.error("--report cannot be used with --dry-run because dry-run writes no files")

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    try:
        report = organize(args.folder, dry_run=args.dry_run, report_path=args.report)
        if args.report:
            report.save_json(args.report.expanduser())
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")

    print(report.summary())
    return 1 if report.errors else 0
