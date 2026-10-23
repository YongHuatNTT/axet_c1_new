"""``logscope timeline`` command implementation."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Union

from .parser import iter_log_records

BAR_CHAR = "#"
MAX_BAR_WIDTH = 50


def parse_bucket_interval(bucket: str) -> timedelta:
    """Parse a bucket spec like ``15m`` or ``1h`` into a ``timedelta``.

    Supported suffixes: ``m`` (minutes), ``h`` (hours), ``s`` (seconds).
    """
    if not bucket:
        raise ValueError("bucket interval must not be empty")

    suffix = bucket[-1].lower()
    value_part = bucket[:-1]

    unit_seconds = {"s": 1, "m": 60, "h": 3600}
    if suffix not in unit_seconds:
        raise ValueError(
            f"invalid bucket interval '{bucket}': unit must be one of s, m, h"
        )

    try:
        value = int(value_part)
    except ValueError as exc:
        raise ValueError(f"invalid bucket interval '{bucket}': {exc}") from exc

    if value <= 0:
        raise ValueError(f"invalid bucket interval '{bucket}': value must be positive")

    return timedelta(seconds=value * unit_seconds[suffix])


def floor_timestamp(timestamp: datetime, interval: timedelta) -> datetime:
    """Floor ``timestamp`` to the start of its bucket for ``interval``."""
    interval_seconds = int(interval.total_seconds())
    if interval_seconds <= 0:
        raise ValueError("bucket interval must be positive")

    epoch = datetime(timestamp.year, timestamp.month, timestamp.day)
    elapsed_seconds = int((timestamp - epoch).total_seconds())
    bucket_start_seconds = (elapsed_seconds // interval_seconds) * interval_seconds
    return epoch + timedelta(seconds=bucket_start_seconds)


@dataclass
class TimelineResult:
    bucket_spec: str = ""
    buckets: List[Tuple[datetime, int]] = field(default_factory=list)
    malformed_count: int = 0

    def to_dict(self) -> dict:
        return {
            "bucket": self.bucket_spec,
            "malformed_count": self.malformed_count,
            "buckets": [
                {"start": start.strftime("%Y-%m-%d %H:%M:%S"), "error_count": count}
                for start, count in self.buckets
            ],
        }


def compute_timeline(path: Union[str, Path], bucket: str) -> TimelineResult:
    """Stream ``path`` once and group ERROR records into time buckets."""
    interval = parse_bucket_interval(bucket)
    result = TimelineResult(bucket_spec=bucket)
    counts: Counter = Counter()

    for record, _raw_line in iter_log_records(path):
        if record is None:
            result.malformed_count += 1
            continue
        if record.level != "ERROR":
            continue
        bucket_start = floor_timestamp(record.timestamp, interval)
        counts[bucket_start] += 1

    result.buckets = sorted(counts.items(), key=lambda item: item[0])
    return result


def render_timeline_text(result: TimelineResult) -> str:
    lines = [
        "logscope timeline",
        "==================",
        f"Bucket size: {result.bucket_spec}",
        "",
    ]

    if not result.buckets:
        lines.append("(no ERROR records found)")
    else:
        max_count = max(count for _start, count in result.buckets)
        for start, count in result.buckets:
            bar_len = MAX_BAR_WIDTH if max_count == 0 else int(
                (count / max_count) * MAX_BAR_WIDTH
            )
            bar_len = max(bar_len, 1 if count > 0 else 0)
            bar = BAR_CHAR * bar_len
            label = start.strftime("%Y-%m-%d %H:%M")
            lines.append(f"{label}  {bar} {count}")

    lines.extend(["", f"Malformed lines: {result.malformed_count}"])
    return "\n".join(lines)


def render_timeline_markdown_lines(result: TimelineResult) -> List[str]:
    lines = [f"- Bucket size: {result.bucket_spec}", ""]
    if not result.buckets:
        lines.append("(no ERROR records found)")
    else:
        lines.extend(["| Bucket start | Error count |", "| --- | --- |"])
        lines.extend(
            f"| {start.strftime('%Y-%m-%d %H:%M:%S')} | {count} |"
            for start, count in result.buckets
        )

    lines.extend(["", f"- Malformed line count: {result.malformed_count}"])
    return lines
