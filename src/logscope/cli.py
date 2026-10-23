"""Command-line entry point for logscope."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .grep import compute_grep, render_grep_text
from .summary import compute_summary, render_summary_text
from .timeline import compute_timeline, render_timeline_text

FORMAT_CHOICES = ("text", "json", "md")
LEVEL_CHOICES = ("INFO", "WARN", "ERROR")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="logscope", description="Streaming log analysis CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Summarize a log file")
    summary_parser.add_argument("logfile", help="Path to the log file")
    summary_parser.add_argument(
        "--format", choices=FORMAT_CHOICES, default="text", help="Output format"
    )

    timeline_parser = subparsers.add_parser(
        "timeline", help="Show ERROR counts grouped by time bucket"
    )
    timeline_parser.add_argument("logfile", help="Path to the log file")
    timeline_parser.add_argument(
        "--bucket", default="15m", help="Bucket interval, e.g. 15m, 1h, 30s"
    )
    timeline_parser.add_argument(
        "--format", choices=FORMAT_CHOICES, default="text", help="Output format"
    )

    grep_parser = subparsers.add_parser(
        "grep", help="Filter log lines by level and/or since timestamp"
    )
    grep_parser.add_argument("logfile", help="Path to the log file")
    grep_parser.add_argument("--level", choices=LEVEL_CHOICES, default=None)
    grep_parser.add_argument(
        "--since", default=None, help="Only include records at/after 'YYYY-MM-DD HH:MM'"
    )
    grep_parser.add_argument(
        "--format", choices=FORMAT_CHOICES, default="text", help="Output format"
    )

    return parser


def run_summary(logfile: str, output_format: str) -> int:
    try:
        result = compute_summary(logfile)
    except FileNotFoundError:
        print(f"logscope: error: log file not found: {logfile}", file=sys.stderr)
        return 1

    if output_format == "text":
        print(render_summary_text(result))
        return 0

    print(
        f"logscope: error: --format {output_format} is not supported yet",
        file=sys.stderr,
    )
    return 2


def run_timeline(logfile: str, bucket: str, output_format: str) -> int:
    try:
        result = compute_timeline(logfile, bucket)
    except FileNotFoundError:
        print(f"logscope: error: log file not found: {logfile}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"logscope: error: {exc}", file=sys.stderr)
        return 2

    if output_format == "text":
        print(render_timeline_text(result))
        return 0

    print(
        f"logscope: error: --format {output_format} is not supported yet",
        file=sys.stderr,
    )
    return 2


def run_grep(logfile: str, level: Optional[str], since: Optional[str], output_format: str) -> int:
    try:
        result = compute_grep(logfile, level=level, since=since)
    except FileNotFoundError:
        print(f"logscope: error: log file not found: {logfile}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"logscope: error: {exc}", file=sys.stderr)
        return 2

    if output_format == "text":
        print(render_grep_text(result))
        return 0

    print(
        f"logscope: error: --format {output_format} is not supported yet",
        file=sys.stderr,
    )
    return 2


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "summary":
        return run_summary(args.logfile, args.format)
    if args.command == "timeline":
        return run_timeline(args.logfile, args.bucket, args.format)
    if args.command == "grep":
        return run_grep(args.logfile, args.level, args.since, args.format)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
