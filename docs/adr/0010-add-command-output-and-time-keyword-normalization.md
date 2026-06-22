# 10. Add Command Output and Time Keyword Normalization

## Status

Accepted

## Context

The `todo add` and `event add` commands currently display the user's original input in the output message, without normalizing relative keywords. For example:

```bash
$ timeline-cli todo add "Review PR" --date today
[txxxx] Added: Review PR (today)
```

This causes several issues:

1. **Ambiguity**: "today" is a relative keyword that changes meaning over time. A user reading the output later may not know which specific date was meant.
2. **Inconsistency**: `event add` output format differs from `todo add` and does not display the date at all: `[exxxx] Added: Review PR at 14:00`.
3. **No explicit "no value" marker**: When time is omitted, the output shows `(date)` without indicating whether time was intentionally unset.

Additionally, users may want to use `--time now` to capture the current time, but this is currently not supported. The keyword `now` exists in the system for `--range` but has different semantics (full datetime vs. time-only).

## Decision

### 1. Scope

Apply changes to:
- `todo add`, `event add`
- `todo edit --new-time`, `event edit --new-time`

### 2. Normalize Output to Explicit Values

All `add` commands will output normalized, explicit values:

| Scenario | Output Format |
|----------|---------------|
| Has date and time | `[id] Added: text (YYYY-MM-DD HH:MM)` |
| Has date, no time | `[id] Added: text (YYYY-MM-DD no-time)` |
| No date (undated todo) | `[id] Added: text (undated)` |

**Examples:**

```bash
$ timeline-cli todo add "Review PR" --date today --time now
[txxxx] Added: Review PR (2026-06-22 14:30)

$ timeline-cli todo add "Write tests" --date today
[txxxx] Added: Write tests (2026-06-22 no-time)

$ timeline-cli todo add "Someday task" --date ?
[txxxx] Added: Someday task (undated)

$ timeline-cli event add "Meeting" --date today --time 15:00
[exxxx] Added: Meeting (2026-06-22 15:00)
```

### 3. Keyword Support

| Parameter | Supported Keywords | Resolves To | Constraint |
|-----------|-------------------|-------------|------------|
| `--date` | `today`, `yesterday`, `tomorrow`, `YYYY-MM-DD`, `?` | `YYYY-MM-DD` | Does NOT support `now` |
| `--time` | `now`, `HH:MM` | `HH:MM` | `now` only valid when date is today |
| `--range` | `now`, `today`, etc. | datetime or date | No additional constraints |

### 4. `now` Semantics by Context

Accept context-dependent semantics for `now`:

- `--time now` → resolves to current time (`HH:MM`)
- `--range ..now` → resolves to full datetime (date + time)

This ambiguity is acceptable because the parameter context (`--time` vs `--range`) clearly disambiguates.

### 5. Constraint: `--time now` Requires Today

`--time now` (and `--new-time now`) is only valid when the associated date equals today's date.

**Validation:**
- For `add`: check `--date` value
- For `edit`: check the existing item's date

**Error message when constraint violated:**

```
Error: '--time now' can only be used when the date is today.
Current date is 2026-06-22, but specified date is 2026-06-20.
```

**Error message for `--date now`:**

```
Error: '--date' does not support 'now'. Use 'today' instead.
```

## Consequences

### Positive

- **Clarity**: Output always shows explicit, unambiguous values.
- **Consistency**: `todo add` and `event add` have uniform output format.
- **User convenience**: `--time now` allows quick capture of current time.
- **Semantic safety**: Constraint on `now` prevents illogical combinations (e.g., "yesterday at now").

### Negative

- **Implementation complexity**: Requires date validation for `--time now`.
- **Potential user confusion**: `now` has different meanings in different contexts, though parameter context disambiguates.

### Migration

No data migration required. Only affects CLI output and argument parsing.