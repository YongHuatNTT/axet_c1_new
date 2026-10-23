# PLAN: logscope Implementation Plan

## 1. Architecture

### 1.1 Layers
- **Parser layer** (`parser.py`)
  - Streaming line reader (generator)
  - Single-line parser + validation
  - Malformed-line counting
- **Command layer** (`summary.py`, `timeline.py`, `grep.py`, `cli.py`)
  - Command-specific aggregation/filtering logic
  - Input validation (`--bucket`, `--since`, level)
- **Formatting layer** (`formatter.py`)
  - Text output (default)
  - JSON output (`--format json`)
  - Markdown report file output (`--format md`)

### 1.2 Data Flow
1. CLI parses args
2. Command requests streaming records from parser
3. Command computes result in one pass
4. Formatter renders result to selected format
5. For markdown mode, formatter writes report file and returns path

### 1.3 Streaming Guarantees
- Open file once and iterate line-by-line
- Never keep all log lines in memory
- Only bounded in-memory structures:
  - counters
  - top error frequency map
  - timeline bucket map

## 2. File Structure

```text
src/
  logscope/
    __init__.py
    cli.py
    parser.py
    summary.py
    timeline.py
    grep.py
    formatter.py

tests/
  test_parser.py
  test_summary.py
  test_timeline.py
  test_grep.py

scripts/
  gen_log.py

SPEC.md
PROJECT_INSTRUCTIONS.md
PLAN.md
README.md
sample.log
PERFORMANCE.md
```

## 3. Command Implementation Plan

### 3.1 `logscope summary <logfile>`
Compute in one pass:
- INFO/WARN/ERROR counts
- error message frequency map -> top 5
- first timestamp and last timestamp from valid records
- malformed-line count

Output targets:
- text summary
- JSON object
- markdown report file

### 3.2 `logscope timeline <logfile> --bucket 15m`
- Validate bucket (`15m` required now; extensible parser)
- For `ERROR` lines only, floor timestamps to 15-minute bucket
- Count per bucket, chronological sort
- Render text bar chart
- Include malformed-line count

Output targets:
- text chart
- JSON bucket series
- markdown report file

### 3.3 `logscope grep <logfile> [--level LEVEL] [--since "YYYY-MM-DD HH:MM"]`
- Optional level filter (`INFO|WARN|ERROR`)
- Optional since filter parsed as `%Y-%m-%d %H:%M`
- Stream and emit only matching valid lines
- Skip malformed lines and count them

Output targets:
- text lines + malformed count
- JSON with matched lines + counts
- markdown report file

## 4. Error Handling Strategy
- File missing/unreadable -> clear error + non-zero exit code
- Invalid level/bucket/since -> clear validation error + non-zero exit code
- Malformed lines -> continue processing; increment malformed counter
- Empty valid-result scenarios -> explicit empty output with counts

## 5. Testing Strategy

### 5.1 Unit Test Scope
- **Parser tests**
  - valid parsing
  - invalid timestamp
  - invalid level
  - missing fields/message
  - malformed counter correctness
- **Summary tests**
  - level counts
  - top-5 errors
  - first/last timestamps
  - malformed counting
- **Timeline tests**
  - 15m bucketing correctness
  - ERROR-only grouping
  - chart/bucket output checks
  - malformed counting
- **Grep tests**
  - level filter
  - since filter boundary (`>=`)
  - combined filters
  - malformed skipping/counting

### 5.2 Format Tests
- Each command with `--format json`
- Each command with `--format md` and report file creation assertion

## 6. Performance Strategy

### 6.1 Generator Script
- `scripts/gen_log.py` will create ~100 MB synthetic logs with mix:
  - INFO
  - WARN
  - ERROR
  - malformed entries
- Configurable target size and deterministic seed option

### 6.2 Benchmark Procedure
- Run summary/timeline/grep against generated file
- Capture:
  - elapsed runtime
  - file size
  - memory signal (RSS/`/usr/bin/time -v` if available)
  - command line used
  - environment details (WSL Ubuntu, Python version)
- Document in `PERFORMANCE.md`

### 6.3 Acceptance Targets
- 100 MB processing under 60 seconds
- memory remains stable (no unbounded growth)

## 7. Phase-by-Phase Execution

### Phase 1 (Docs + Plan)
- Create/verify: `SPEC.md`, `PROJECT_INSTRUCTIONS.md`, `README.md`, `sample.log`, `PLAN.md`
- Run tests (or verify no tests exist yet)
- `git add .`
- `git commit -m "docs: add specification and implementation plan"`
- verify with `git log --oneline -n 5`

### Phase 2 (Parser)
- Implement streaming parser + malformed handling
- Add parser tests
- run tests
- commit: `feat: implement streaming log parser`

### Phase 3 (Summary)
- Implement summary command
- add tests
- run tests
- commit: `feat: add summary command`

### Phase 4 (Timeline)
- Implement timeline command
- add tests
- run tests
- commit: `feat: add timeline command`

### Phase 5 (Grep)
- Implement grep command
- add tests
- run tests
- commit: `feat: add grep command`

### Phase 6 (Formats)
- Implement `--format json` and `--format md`
- ensure markdown writes report files
- add tests
- run tests
- commit: `feat: add output format support`

### Phase 7 (Performance)
- Implement `scripts/gen_log.py`
- generate ~100 MB file
- run benchmark and collect metrics
- write `PERFORMANCE.md`
- commit: `perf: add large log benchmark`

## 8. Completion Checklist Mapping
- summary/timeline/grep behavior -> phases 3/4/5
- malformed counting -> phases 2–6 tests
- json/md outputs + report generation -> phase 6
- 100 MB speed + stable memory -> phase 7
- incremental history evidence -> commit after every phase
