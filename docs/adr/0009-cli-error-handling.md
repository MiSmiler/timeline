# CLI Error Handling Standard

Timeline CLI uses a two-tier error handling system: user-correctable errors (exit code 1) and internal errors (exit code 2). This separation helps users distinguish between "my mistake" and "tool bug," and enables better scripting with exit codes.

## Exception Hierarchy

```
TimelineError (base)
├── TimelineFileNotFoundError (exit 1)
├── TimelineValidationError (exit 1)
└── TimelineInternalError (exit 2)
```

## Error Message Format

Single line: `{error message}. {suggestion}`

Example: `Timeline file not found. Run 'timeline-cli init' to create one.`

## Error Scenarios

| Scenario | Exception | Message | Status |
|----------|-----------|---------|--------|
| `.timelines.jsonl` not found | `TimelineFileNotFoundError` | "Timeline file not found. Run 'timeline-cli init' to create one." | ✅ Implemented |
| Invalid date format | `TimelineValidationError` | "Invalid date: {input}. Use YYYY-MM-DD format." | ✅ Implemented |
| Invalid time format | `TimelineValidationError` | "Invalid time: {input}. Use HH:MM format." | 🔲 Planned (doctor validation only) |
| Todo ID not found | `TimelineValidationError` | "Todo not found: {id}" | ✅ Implemented |
| Event ID not found | `TimelineValidationError` | "Event not found: {id}" | ✅ Implemented |
| Note already exists for date | `TimelineValidationError` | "Note already exists for {date}" | 🔲 Planned |
| JSON parse failure (corrupted file) | `TimelineInternalError` | "Failed to parse timeline file. Run 'timeline-cli doctor --fix' to repair." | ✅ Implemented |
| Schema version incompatible | `TimelineInternalError` | "Unsupported schema version: {version}. Please upgrade timeline-cli." | 🔲 Planned |
| Timeline file already exists | `TimelineValidationError` | "Timeline file already exists: {path}" | ✅ Implemented (init) |
| Doctor validation failed | `TimelineValidationError` | "Found {n} validation errors" | ✅ Implemented (doctor) |

## Global `--debug` Flag

`timeline-cli --debug <command>` shows full Python stack trace for internal errors. Useful for bug reports.

## Considered Options

**Option A: Unified handling** — All errors use exit code 1, no distinction. Simpler but less helpful for scripting and debugging.

**Option B (chosen): Two-tier handling** — Separate user-correctable vs internal errors. Matches industry practice (git, docker, cargo).

## Consequences

- Exit code 1 = user should fix something
- Exit code 2 = potential tool bug, user may need to report or repair
- Scripts can check `$?` to handle errors programmatically
- Future commands should raise appropriate exception types