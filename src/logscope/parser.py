"""Streaming log parser for logscope.

Log line format:
    YYYY-MM-DD HH:MM:SS LEVEL Message text...

This module never loads a whole file into memory. ``iter_log_records``
yields one record (or ``None`` for malformed lines) at a time, so callers
can process arbitrarily large files with bounded memory usage.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Tuple, Union

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
VALID_LEVELS = ("INFO", "WARN", "ERROR")


@dataclass(frozen=True)
class LogRecord:
    """A single successfully parsed log line."""

    timestamp: datetime
    level: str
    message: str
    raw: str


def parse_line(line: str) -> Optional[LogRecord]:
    """Parse a single raw log line.

    Returns a :class:`LogRecord` on success, or ``None`` if the line is
    malformed (missing fields, bad timestamp, or invalid level).
    """
    stripped = line.rstrip("\r\n")
    if stripped.strip() == "":
        return None

    parts = stripped.split(" ", 3)
    if len(parts) < 4:
        return None

    date_part, time_part, level, message = parts
    if level not in VALID_LEVELS:
        return None

    try:
        timestamp = datetime.strptime(f"{date_part} {time_part}", TIMESTAMP_FORMAT)
    except ValueError:
        return None

    return LogRecord(timestamp=timestamp, level=level, message=message, raw=stripped)


def iter_raw_lines(path: Union[str, Path]) -> Iterator[str]:
    """Stream raw lines from ``path`` one at a time, never buffering the file."""
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            yield raw_line.rstrip("\r\n")


def iter_log_records(path: Union[str, Path]) -> Iterator[Tuple[Optional[LogRecord], str]]:
    """Stream ``(record, raw_line)`` pairs from ``path``.

    ``record`` is ``None`` for malformed (non-blank) lines. Blank lines are
    silently skipped and never counted as malformed. Callers are expected to
    keep their own running malformed-line counter by checking ``record is
    None``.
    """
    for raw_line in iter_raw_lines(path):
        if raw_line.strip() == "":
            continue
        yield parse_line(raw_line), raw_line
