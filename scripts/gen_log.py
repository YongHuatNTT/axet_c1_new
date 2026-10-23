"""Generate a synthetic log file for benchmarking logscope.

Usage:
    python3 scripts/gen_log.py --target-mb 100 --output bench.log

Produces a log with a realistic mix of INFO, WARN, ERROR and a small
percentage of malformed lines, streamed directly to disk so the generator
itself never buffers the whole file in memory.
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

LEVEL_WEIGHTS = [
    ("INFO", 70),
    ("WARN", 20),
    ("ERROR", 10),
]

INFO_MESSAGES = [
    "Application started",
    "User login successful",
    "Health check passed",
    "Background job completed",
    "Session refreshed",
    "Cache warmed up",
    "Request processed successfully",
]

WARN_MESSAGES = [
    "Slow response detected",
    "Cache miss spike",
    "Slow query detected",
    "Retrying failed request",
    "Queue depth increasing",
]

ERROR_MESSAGES = [
    "Database connection failed",
    "Timeout while calling payment API",
    "Disk space critically low",
    "Unhandled exception in worker",
    "Downstream service unavailable",
]

MALFORMED_LINES = [
    "this line has no timestamp or level",
    "2026-10-01 09:00:00 DEBUG unsupported level value",
    "2026-10-01 BADTS ERROR broken timestamp example",
    "",
]

MALFORMED_RATE = 0.01
BYTES_PER_MB = 1024 * 1024


def _weighted_level(rng: random.Random) -> str:
    total = sum(weight for _level, weight in LEVEL_WEIGHTS)
    roll = rng.uniform(0, total)
    cumulative = 0.0
    for level, weight in LEVEL_WEIGHTS:
        cumulative += weight
        if roll <= cumulative:
            return level
    return LEVEL_WEIGHTS[-1][0]


def _message_for_level(rng: random.Random, level: str) -> str:
    if level == "INFO":
        return rng.choice(INFO_MESSAGES)
    if level == "WARN":
        return rng.choice(WARN_MESSAGES)
    return rng.choice(ERROR_MESSAGES)


def generate_log(output_path: Path, target_mb: float, seed: int = 42) -> int:
    """Stream a synthetic log of roughly ``target_mb`` megabytes to disk.

    Returns the number of lines written. Never buffers the full file.
    """
    rng = random.Random(seed)
    target_bytes = int(target_mb * BYTES_PER_MB)
    timestamp = datetime(2026, 10, 1, 0, 0, 0)
    line_count = 0
    bytes_written = 0

    with open(output_path, "w", encoding="utf-8") as handle:
        while bytes_written < target_bytes:
            if rng.random() < MALFORMED_RATE:
                line = rng.choice(MALFORMED_LINES)
            else:
                level = _weighted_level(rng)
                message = _message_for_level(rng, level)
                ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                line = f"{ts_str} {level} {message}"
                timestamp += timedelta(seconds=rng.randint(1, 5))

            handle.write(line + "\n")
            bytes_written += len(line) + 1
            line_count += 1

    return line_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic logscope benchmark log")
    parser.add_argument("--target-mb", type=float, default=100.0, help="Target file size in MB")
    parser.add_argument("--output", type=str, default="bench.log", help="Output file path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for determinism")
    args = parser.parse_args()

    output_path = Path(args.output)
    line_count = generate_log(output_path, args.target_mb, seed=args.seed)
    size_mb = output_path.stat().st_size / BYTES_PER_MB
    print(f"Wrote {line_count} lines, {size_mb:.2f} MB -> {output_path}")


if __name__ == "__main__":
    main()
