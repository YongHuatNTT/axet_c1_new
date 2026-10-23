"""``logscope summary`` command implementation."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

from .parser import iter_log_records

TOP_ERROR_LIMIT = 5


@dataclass
class SummaryResult:
    info_count: int = 0
    warn_count: int = 0
    error_count: int = 0
    malformed_count: int = 0
    first_timestamp: Optional[datetime] = None
    last_timestamp: Optional[datetime] = None
    top_errors: List[Tuple[str, int]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "info_count": self.info_count,
            "warn_count": self.warn_count,
            "error_count": self.error_count,
            "malformed_count": self.malformed_count,
            "first_timestamp": (
                self.first_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if self.first_timestamp
                else None
            ),
            "last_timestamp": (
                self.last_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if self.last_timestamp
                else None
            ),
            "top_errors": [
                {"message": message, "count": count} for message, count in self.top_errors
            ],
        }


def compute_summary(path: Union[str, Path]) -> SummaryResult:
    """Stream ``path`` once and compute summary statistics.

    Only bounded in-memory structures are used: scalar counters, a frequency
    map of error messages, and running first/last timestamps.
    """
    result = SummaryResult()
    error_frequency: Counter = Counter()

    for record, _raw_line in iter_log_records(path):
        if record is None:
            result.malformed_count += 1
            continue

        if record.level == "INFO":
            result.info_count += 1
        elif record.level == "WARN":
            result.warn_count += 1
        elif record.level == "ERROR":
            result.error_count += 1
            error_frequency[record.message] += 1

        if result.first_timestamp is None or record.timestamp < result.first_timestamp:
            result.first_timestamp = record.timestamp
        if result.last_timestamp is None or record.timestamp > result.last_timestamp:
            result.last_timestamp = record.timestamp

    result.top_errors = sorted(
        error_frequency.items(), key=lambda item: (-item[1], item[0])
    )[:TOP_ERROR_LIMIT]
    return result


def render_summary_text(result: SummaryResult) -> str:
    lines = [
        "logscope summary",
        "================",
        f"INFO count:  {result.info_count}",
        f"WARN count:  {result.warn_count}",
        f"ERROR count: {result.error_count}",
        "",
        "Top 5 error messages:",
    ]
    if result.top_errors:
        for message, count in result.top_errors:
            lines.append(f"  {count:>5}  {message}")
    else:
        lines.append("  (none)")

    first_ts = (
        result.first_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if result.first_timestamp
        else "N/A"
    )
    last_ts = (
        result.last_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if result.last_timestamp
        else "N/A"
    )
    lines.extend(
        [
            "",
            f"First timestamp: {first_ts}",
            f"Last timestamp:  {last_ts}",
            "",
            f"Malformed lines: {result.malformed_count}",
        ]
    )
    return "\n".join(lines)
