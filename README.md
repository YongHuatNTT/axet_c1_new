# logscope

A streaming Python CLI for log analysis. See `SPEC.md` for the full functional
specification, `PROJECT_INSTRUCTIONS.md` for workflow rules, and `PLAN.md` for
the phased implementation plan.

## Features
- `summary`: level counts, top-5 error messages, first/last timestamps, malformed count
- `timeline`: ERROR counts grouped by time bucket with a text bar chart
- `grep`: filter logs by level and/or `--since` timestamp
- Output formats: `text` (default), `json`, `md` (writes a markdown report file)
- Streams files line-by-line; never loads a whole log into memory (handles ~100 MB+ files)
- Malformed lines are skipped and counted, never crash the tool

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

Valid levels: `INFO`, `WARN`, `ERROR`.

## Installation / running
No external dependencies are required (standard library only). Run the CLI
module directly with `src/` on `PYTHONPATH`:

```bash
PYTHONPATH=src python3 -m logscope.cli summary sample.log
PYTHONPATH=src python3 -m logscope.cli timeline sample.log --bucket 15m
PYTHONPATH=src python3 -m logscope.cli grep sample.log --level ERROR --since "2026-10-01 09:00"
```

## Global format option
```bash
--format text   # default, human-readable
--format json   # machine-readable JSON to stdout
--format md     # writes logscope_<command>_<timestamp>.md report file
```

## Running tests
This environment does not have `pytest`/`pip` installed, so tests are written
with the Python standard library `unittest` framework (test discovery still
uses `test_*.py` files under `tests/`):

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Performance benchmark
`scripts/gen_log.py` generates a synthetic log of a target size for
benchmarking. Results for a ~100 MB file are documented in `PERFORMANCE.md`.

```bash
python3 scripts/gen_log.py --target-mb 100 --output /tmp/bench.log
PYTHONPATH=src python3 -m logscope.cli summary /tmp/bench.log
```

## Project layout
```text
src/logscope/
  parser.py      # streaming parser + malformed-line detection
  summary.py      # summary command
  timeline.py     # timeline command
  grep.py         # grep command
  formatter.py    # json rendering + markdown report writer
  cli.py          # argparse entry point
tests/            # unittest suite (parser, summary, timeline, grep, formatter)
scripts/gen_log.py # synthetic log generator for benchmarking
```

## Project docs
- `SPEC.md` — functional specification
- `PROJECT_INSTRUCTIONS.md` — workflow and constraints
- `PLAN.md` — phased implementation plan
- `PERFORMANCE.md` — benchmark results on a ~100 MB log
