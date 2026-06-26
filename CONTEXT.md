# CONTEXT

## Event

A record of something that happened at a specific point in time. An Event always belongs to a single date and has a time of day.

Fields: id (int), date (YYYY-MM-DD), time (HH:MM), text (str, may contain `\n`).

Examples:
- "just fixed a bug" → `event add --at now`
- "had a standup at 2pm" → `event add --at todayT14:00`

In the CLI, the user-facing ID is `e` + number (e.g. `e1`, `e42`). In storage, only the number is stored.

## Note

A textual note for a date. A Note belongs to a single date. It has no time component — if a user specifies a time when creating a note, that is an error.

Fields: id (int), date (YYYY-MM-DD), text (str, may contain `\n`).

Examples:
- "the weather is nice today"
- "project hit a bottleneck"
- "go to bed early tonight"

In the CLI, the user-facing ID is `n` + number (e.g. `n1`, `n42`). In storage, only the number is stored.

## ID

An incrementing integer shared across Event and Note. The next ID is derived by scanning the file at write time (max existing id + 1). No next_id counter is stored — the ID sequence is always derived from the data.

## TimePoint

A point-in-time value object parsed from a user-supplied time expression string. Resolves relative expressions (`today`, `now`, `yesterday`, `todayT14:00`) to concrete date and optional time at parse time.

Used by: event add, note add, event edit --new-at, note edit --new-at, diary.

## DateRange

A date range value object parsed from a user-supplied range expression. Supports: single date (`today`), closed range (`2026-06-20..2026-06-26`), open-ended range (`..2026-06-26`, `2026-06-20..`), and unbounded (`..`).

Used by: event list --at, note list --at.

## Diary

A single-date view that aggregates all Events and Notes for one date. Events are shown under `## Events` sorted by time ascending, Notes under `## Notes` sorted by id ascending. Both sections are always shown, even when empty.

CLI: `timeline-cli diary [date]` — defaults to today. No --json flag.

## Dates

Lists all dates that have data. Output is markdown with dates in descending order.

CLI: `timeline-cli dates`
