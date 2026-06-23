# ADR-0012: Unified Time Expression System

## Status

Accepted

## Context

The previous parameter system for `todo list` and `event list` had several issues:

1. **`--range` required**: Users had to specify `--range` for every list command, even for common cases like "today".
2. **`--range` syntax unclear**: The `..` separator and `?` for undated were not intuitive.
3. **`--time` parameter ambiguous**: Only existed for `todo list`, but its semantics were unclear.
4. **Inconsistent parameters**: `todo list` had `--time`/`--status`, but `event list` didn't.
5. **Separate parsing logic**: Todo and event commands each implemented their own time parsing.

## Decision

Introduce a unified **TimeExpr** abstraction with **Timepoint** and **Timerange** concepts, replacing `--range` and `--time` with a single `--at` parameter.

### TimeExpr

Unified time expression parsing layer. Shared by all commands. Contains either a Timepoint or a Timerange.

### Timepoint Components

| date | time | Example | Meaning |
|------|------|---------|---------|
| Yes | Yes | `2026-06-23T09:00`, `todayT09:00` | Precise point |
| Yes | No | `2026-06-23`, `today` | A day |
| No | Yes | `09:00` | Auto-fill date=today |
| No | No | Empty | Boundary marker |
| Special | - | `undated`, `now` | No date / Current time |

### Timerange

Format: `timepoint..timepoint`

Expansion rules:
- Left has date only → `dateT00:00`
- Right has date only → `dateT23:59`
- Time only → Auto-fill date=today
- Empty → Start/end boundary

Constraint: `left < right` (reversed ranges rejected).

### Command-Specific Semantics

| Command | Date-only Timepoint | `undated` | `now` |
|---------|---------------------|-----------|-------|
| `todo list` | Full day range | No-date todos | Current time |
| `todo add/edit` | Set date only | Create no-date | Current time |
| `event list` | Full day range | Error | Current time |
| `event add/edit` | Error (requires time) | Error | Current time |

### New Parameter System

- `--at`: Time expression (Timepoint or Timerange). Replaces `--range` and `--time`.
- `--no-time`: Filter todos without time (Todo only).
- `--status`: Filter by status (Todo only).
- `--contains`: Filter by text substring (Todo and Event).

### Execution Rules

1. `todo list` and `event list` require at least one parameter (`--at`, `--no-time`, `--status`, `--contains`).
2. If no time filter specified, default range is `..` (all dates).
3. `--no-time` requires `--at` to be Timerange (not Timepoint).

### Examples

```bash
# Timepoint examples
timeline-cli todo list --at today
timeline-cli todo list --at todayT09:00
timeline-cli todo list --at 09:00
timeline-cli todo add "task" --at undated
timeline-cli event add "meeting" --at now

# Timerange examples
timeline-cli todo list --at ..
timeline-cli todo list --at yesterday..today
timeline-cli todo list --at 2026-06-23..2026-06-25
timeline-cli todo list --at 2026-06-23T09:00..todayT17:00

# Combined filters
timeline-cli todo list --at .. --status pending
timeline-cli todo list --at today --no-time
timeline-cli todo list --contains "meeting"

# Parameter-only (default range=..)
timeline-cli todo list --status pending
timeline-cli todo list --no-time
```

## Consequences

### Positive

- Unified parameter system reduces cognitive load.
- `--at` covers all time-based needs (point and range).
- Single parsing layer avoids duplicate implementation.
- Clear semantics for each command.
- Removed unintuitive symbols (`?` for undated).

### Negative

- Requires migration from existing `--range` and `--time` usage.
- `T` separator may feel unfamiliar initially.
- More complex parsing logic with component combinations.

### Migration

- Replace `--range` with `--at`.
- Replace `--time HH:MM` with `--at HH:MM` or `--at todayTHH:MM`.
- Replace `--range ?` with `--at undated`.
- Event add/edit must now always include time component.