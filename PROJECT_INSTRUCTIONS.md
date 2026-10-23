# PROJECT_INSTRUCTIONS: logscope

## Objective
Build `logscope`, a Python CLI log-analysis tool with streaming processing, robust malformed-line handling, and multi-format output.

## Execution Environment
- Development shell commands must run inside WSL:

```bash
wsl -d Ubuntu --cd /mnt/c/Users/yonghuat.chai/Documents/assignment/axet_c1_new -- <command>
```

## Development Workflow (Mandatory)
1. Follow plan-then-build.
2. Implement in milestones/phases.
3. After each completed milestone:
   - run tests
   - verify results
   - `git add .`
   - commit with descriptive message
4. Never make one giant commit.
5. Keep commits aligned with the defined phase boundaries.

## Functional Scope
Implement CLI commands:
- `summary`
- `timeline`
- `grep`

with global formatting options:
- `--format json`
- `--format md`

## Core Constraints
- Stream file line-by-line
- Never load full log into memory
- Malformed lines must not crash execution
- Malformed lines must be counted
- Must handle approximately 100 MB logs

## Log Schema
Valid line format:

```text
YYYY-MM-DD HH:MM:SS LEVEL Message
```

Levels allowed: `INFO`, `WARN`, `ERROR`

## Quality and Verification
- Unit tests required for parser and each command.
- Include malformed-input tests.
- Confirm acceptance checklist before final completion.

## Output Artifacts
Required files and directories:
- `SPEC.md`
- `PROJECT_INSTRUCTIONS.md`
- `PLAN.md`
- `README.md`
- `sample.log`
- source package(s)
- `tests/`
- `scripts/`
- `PERFORMANCE.md`

## Git Commit Milestones (Target Messages)
- `docs: add specification and implementation plan`
- `feat: implement streaming log parser`
- `feat: add summary command`
- `feat: add timeline command`
- `feat: add grep command`
- `feat: add output format support`
- `perf: add large log benchmark`

## Acceptance Criteria
- `summary` works on `sample.log`
- `timeline` works on `sample.log`
- `grep` works on `sample.log`
- parser tests pass
- summary tests pass
- timeline tests pass
- grep tests pass
- malformed-line counting works
- 100 MB log processed in under 60 seconds
- memory remains stable
- git history shows multiple incremental commits
