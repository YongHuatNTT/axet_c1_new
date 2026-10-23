# logscope

A streaming Python CLI for log analysis.

## Features
- `summary`: level counts, top errors, first/last timestamps, malformed count
- `timeline`: error counts by time bucket with text bar chart
- `grep`: filter logs by level and since timestamp
- Output formats: text (default), json, markdown report
- Handles large files (~100 MB) by streaming line-by-line

## Log format
```text
YYYY-MM-DD HH:MM:SS LEVEL Message
```

Example:
```text
2026-10-01 09:00:00 INFO Application started
2026-10-01 09:01:00 WARN Slow response detected
2026-10-01 09:02:00 ERROR Database connection failed
```

## Planned commands
```bash
logscope summary sample.log
logscope timeline sample.log --bucket 15m
logscope grep sample.log --level ERROR --since "2026-10-01 09:00"
```

## Global format option
```bash
--format json
--format md
```

## Project docs
- `SPEC.md` — functional specification
- `PROJECT_INSTRUCTIONS.md` — workflow and constraints
- `PLAN.md` — phased implementation plan
