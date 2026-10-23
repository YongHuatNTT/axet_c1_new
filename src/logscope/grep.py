"""``logscope grep`` command implementation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from .parser import LogRecord, VALID_LEVELS, iter_log_records

SINCE_FORMAT = "%Y-%m-%d %H:%M"


def parse_since(value: str) -> datetime:
    """Parse a ``--since`` value formatted as ``YYYY-MM-DD HH:MM``."""
    try:
        return datetime.strptime(value, SINCE_FORMAT)
    except ValueError as exc:
        raise ValueError(
            f"invalid --since value '{value}': expected format 'YYYY-MM-DD HH:MM'"
        ) from exc


def validate_level(level: Optional[str]) -> Optional[str]:
    if level is None:
        return None
    if level not in VALID_LEVELS:
        raise ValueError(
            f"invalid --level value '{level}': must be one of {', '.join(VALID_LEVELS)}"
        )
    return level


@dataclass
class GrepResult:
    matches: List[LogRecord] = field(default_factory=list)
    malformed_count: int = 0

    def to_dict(self) -> dict:
        return {
            "malformed_count": self.malformed_count,
            "match_count": len(self.matches),
            "matches": [
                {
                    "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "level": record.level,
                    "message": record.message,
                }
                for record in self.matches
            ],
        }


def compute_grep(
    path: Union[str, Path],
    level: Optional[str] = None,
    since: Optional[str] = None,
) -> GrepResult:
    """Stream ``path`` once, filtering valid records by level and/or since."""
    level = validate_level(level)
    since_dt = parse_since(since) if since else None

    result = GrepResult()
    for record, _raw_line in iter_log_records(path):
        if record is None:
            result.malformed_count += 1
            continue
        if level is not None and record.level != level:
            continue
        if since_dt is not None and record.timestamp < since_dt:
            continue
        result.matches.append(record)

    return result


def render_grep_text(result: GrepResult) -> str:
    lines = [record.raw for record in result.matches]
    lines.append("")
    lines.append(f"Malformed lines skipped: {result.malformed_count}")
    return "\n".join(lines)


def render_grep_markdown_lines(result: GrepResult) -> List[str]:
    lines = [f"- Match count: {len(result.matches)}", ""]
    if result.matches:
        lines.extend(["| Timestamp | Level | Message |", "| --- | --- | --- |"])
        lines.extend(
            f"| {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {record.level} | {record.message} |"
            for record in result.matches
        )
    else:
        lines.append("(no matching lines)")

    lines.extend(["", f"- Malformed lines skipped: {result.malformed_count}"])
    return lines
