# logscope Functional Specification

## Overview
`logscope` is a Python CLI tool for analyzing application logs in a streaming, memory-efficient way. It must process large files (including ~100 MB) line-by-line and remain robust in the presence of malformed records.

## CLI Name
- `logscope`

## Log Input Format
Each valid log line must follow:

```text
YYYY-MM-DD HH:MM:SS LEVEL Message text...
```

Example:

```text
2026-10-01 09:00:00 INFO Application started
2026-10-01 09:01:00 WARN Slow response detected
2026-10-01 09:02:00 ERROR Database connection failed
```

### Timestamp Format
- `YYYY-MM-DD HH:MM:SS`

### Levels
- `INFO`
- `WARN`
- `ERROR`

### Malformed Line Definition
A line is malformed if any of the following are true:
- Missing timestamp, level, or message
- Timestamp not parseable with `%Y-%m-%d %H:%M:%S`
- Level is not one of `INFO|WARN|ERROR`

Malformed lines must:
- Never crash the tool
- Be skipped for calculations requiring valid parsed records
- Be counted and included in output

## Commands

## 1) `logscope summary <logfile>`

### Purpose
Produce high-level statistics for a log file.

### Required Output Fields
- Count of `INFO` lines
- Count of `WARN` lines
- Count of `ERROR` lines
- Top 5 error messages (by frequency, descending)
- First timestamp (earliest valid parsed timestamp encountered)
- Last timestamp (latest valid parsed timestamp encountered)
- Malformed line count

### Notes
- If no valid lines exist, first/last timestamp should be reported as null/empty in structured output and clearly indicated in text output.

## 2) `logscope timeline <logfile> --bucket <interval>`

### Purpose
Show error volume over time, grouped by bucket interval.

### Required Behavior
- Group only `ERROR` records by time bucket
- Print text bar chart for grouped counts
- Report malformed line count

### Bucket Support
- Required initial bucket input: `15m`
- Internal design should allow easy extension (e.g., `5m`, `1h`)

### Bucketing Rule
- Floor each error timestamp to the start of its bucket interval.
- Example for `15m`:
  - `09:14:59` -> `09:00`
  - `09:15:00` -> `09:15`

## 3) `logscope grep <logfile> [--level LEVEL] [--since "YYYY-MM-DD HH:MM"]`

### Purpose
Filter and print matching log lines.

### Filters
- `--level`: filter by one of `INFO|WARN|ERROR`
- `--since`: include only records with timestamp >= provided value
  - Input format: `YYYY-MM-DD HH:MM`
  - Parsed internally as seconds `:00`

### Required Output
- Filtered log lines
- Malformed lines skipped and counted

## Global Options

### `--format json`
- Return machine-readable JSON for each command

### `--format md`
- Generate a markdown report file for each command
- Command should also print the report path or confirmation

### Default Format
- Human-readable text to stdout

## Performance and Memory Requirements
- Must handle ~100 MB logs
- Must stream file line-by-line
- Must never load whole file into memory
- Memory usage should remain stable (size of in-memory structures bounded by aggregation needs)

## Error Handling
- Missing file: clear error message and non-zero exit code
- Invalid `--bucket` or `--since`: clear validation message and non-zero exit code
- Malformed records: counted, skipped, processing continues

## Testing Requirements
Unit tests must cover:
- Parser
- Summary command
- Timeline command
- Grep command

Additional behavior coverage:
- Malformed-line counting
- Format outputs (`json`, `md`) for each command
- Since-filter boundary behavior
- Bucket grouping behavior

## Deliverables
- `SPEC.md`
- `PROJECT_INSTRUCTIONS.md`
- `PLAN.md`
- `README.md`
- `sample.log`
- Source code
- `tests/`
- `scripts/`
- `PERFORMANCE.md`
