"""Command-line entry point for logscope."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .summary import compute_summary, render_summary_text

FORMAT_CHOICES = ("text", "json", "md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="logscope", description="Streaming log analysis CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Summarize a log file")
    summary_parser.add_argument("logfile", help="Path to the log file")
    summary_parser.add_argument(
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "summary":
        return run_summary(args.logfile, args.format)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
