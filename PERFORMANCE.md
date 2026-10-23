# PERFORMANCE.md — logscope Benchmark Results

## Environment
- OS: WSL2 Ubuntu on Windows (`Linux ... 6.18.54.1-microsoft-standard-WSL2 x86_64 GNU/Linux`)
- Python: 3.14.4
- CPU: 14 logical cores available (benchmark is single-threaded)
- Working directory: `/mnt/c/Users/yonghuat.chai/Documents/assignment/axet_c1_new`

## Benchmark File
- Generator: `scripts/gen_log.py --target-mb 100 --output /tmp/bench.log --seed 42`
- File size: `104,857,632` bytes (~100.00 MB)
- Line count: `2,212,036` lines
- Content mix: ~70% INFO, ~20% WARN, ~10% ERROR, ~1% malformed lines (injected deliberately)
- Malformed lines detected by logscope: `16,779`

## Commands and Results

All runs measured with `/usr/bin/time -v` (wall clock + peak RSS) against the 100 MB file above.

| Command | Command line | Wall time | Peak RSS (KB) | Peak RSS (MB) |
| --- | --- | --- | --- | --- |
| `summary` | `python3 -m logscope.cli summary /tmp/bench.log --format text` | 0:33.10 | 16,156 | ~15.8 MB |
| `timeline` | `python3 -m logscope.cli timeline /tmp/bench.log --bucket 15m --format text` | 0:32.73 | 18,480 | ~18.0 MB |
| `grep` | `python3 -m logscope.cli grep /tmp/bench.log --level ERROR --since "2026-10-01 09:00" --format text` | 0:30.40 | 125,416 | ~122.5 MB |

Full `/usr/bin/time -v` output is reproduced below for each run.

### `summary`
```text
Command being timed: "python3 -m logscope.cli summary /tmp/bench.log --format text"
User time (seconds): 32.54
System time (seconds): 0.19
Percent of CPU this job got: 98%
Elapsed (wall clock) time (h:mm:ss or m:ss): 0:33.10
Maximum resident set size (kbytes): 16156
Minor (reclaiming a frame) page faults: 2449
Exit status: 0
```

### `timeline`
```text
Command being timed: "python3 -m logscope.cli timeline /tmp/bench.log --bucket 15m --format text"
User time (seconds): 32.12
System time (seconds): 0.22
Percent of CPU this job got: 98%
Elapsed (wall clock) time (h:mm:ss or m:ss): 0:32.73
Maximum resident set size (kbytes): 18480
Minor (reclaiming a frame) page faults: 3133
Exit status: 0
```

### `grep`
```text
Command being timed: "python3 -m logscope.cli grep /tmp/bench.log --level ERROR --since 2026-10-01 09:00 --format text"
User time (seconds): 29.41
System time (seconds): 0.60
Percent of CPU this job got: 98%
Elapsed (wall clock) time (h:mm:ss or m:ss): 0:30.40
Maximum resident set size (kbytes): 125416
Minor (reclaiming a frame) page faults: 30222
Exit status: 0
```

## Analysis

### Runtime
All three commands complete well under the 60-second acceptance target for a
~100 MB log file (30–33 seconds each on this machine), while performing a
single streaming pass over the file via `iter_log_records`.

### Memory
- `summary` and `timeline` keep memory essentially flat (~16–18 MB RSS)
  regardless of file size, because they only maintain bounded structures:
  scalar counters, an error-frequency `Counter`, and a per-bucket `Counter`.
  Line content is never retained once a record has been counted.
- `grep` has a higher peak RSS (~122 MB) in this specific benchmark because
  the filter (`--level ERROR --since "2026-10-01 09:00"`) matches a large
  fraction of the file (~219k of ~2.2M lines), and `compute_grep` currently
  accumulates matching `LogRecord` objects in a list before rendering. Memory
  scales with the **number of matches**, not with total file size — the raw
  file itself is still streamed line-by-line and never loaded wholesale. For
  highly selective filters, grep memory stays small; for broad filters on
  very large files, a future optimization could stream-print matches
  directly instead of buffering them (left as a documented improvement,
  not required by current acceptance criteria).

### Conclusion
- 100 MB log processed in under 60 seconds: **met** (all three commands).
- Memory remains stable / bounded: **met** for `summary`/`timeline`
  (constant-size aggregates); **bounded by match count** for `grep` (not by
  file size), which still satisfies "never load the entire file into
  memory" since the source file is streamed line-by-line throughout.

## Reproducing

```bash
python3 scripts/gen_log.py --target-mb 100 --output /tmp/bench.log --seed 42
PYTHONPATH=src /usr/bin/time -v python3 -m logscope.cli summary /tmp/bench.log
PYTHONPATH=src /usr/bin/time -v python3 -m logscope.cli timeline /tmp/bench.log --bucket 15m
PYTHONPATH=src /usr/bin/time -v python3 -m logscope.cli grep /tmp/bench.log --level ERROR --since "2026-10-01 09:00"
```
