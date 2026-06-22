# 10. Add Command Output and Time Parameter Design

## Status

Accepted

## Context

The `todo add` and `event add` commands currently use separate `--date` and `--time` parameters. This design has several issues:

1. **Parameter redundancy**: Users must specify both `--date today --time now` when they just want "current moment".
2. **Semantic confusion**: `--time now` only represents time, but users naturally think "now" = current date + current time.
3. **Output inconsistency**: ADR-0010 addressed output normalization, but the parameter structure remains fragmented.
4. **Constraint complexity**: The constraint "`--time now` only valid when date is today" requires cross-parameter validation.

Additionally, users want:
- Quick capture of relative time offsets (e.g., "2 hours ago", "30 minutes later")
- Relative date + explicit time combinations (e.g., "today 15:00")
- Simplified command invocation

## Decision

### 1. Merge `--date` and `--time` into `--at`

Replace separate `--date` and `--time` parameters with a single `--at` parameter that accepts both date and time information.

**Requirement**: `--at` must be explicitly specified. No default value.

### 2. `--at` Parameter Syntax

| Input | Parsed Result | Notes |
|-------|---------------|-------|
| `"2026-06-22 15:00"` | date=2026-06-22, time=15:00 | Explicit datetime |
| `"now"` | date=today, time=current HH:MM | Current moment |
| `"2026-06-22"` | date=2026-06-22, time=None | Date only |
| `"today"` | date=today, time=None | Relative date |
| `"yesterday"` | date=yesterday, time=None | Relative date |
| `"tomorrow"` | date=tomorrow, time=None | Relative date |
| `"today 15:00"` | date=today, time=15:00 | Relative date + explicit time |
| `"yesterday 10:00"` | date=yesterday, time=10:00 | Relative date + explicit time |
| `"tomorrow 09:00"` | date=tomorrow, time=09:00 | Relative date + explicit time |
| `"15:00"` | date=today, time=15:00 | Time only, defaults to today |
| `""` | undated | No date, no time |
| `"+2h"` | date=today, time=now+2h | Relative time offset |
| `"-30m"` | date=today, time=now-30m | Relative time offset |
| `"+2h30m"` | date=today, time=now+2h30m | Combined offset |

### 3. Relative Time Offset Syntax

**Syntax**: `[+/-]<value><unit>[<value><unit>]`

**Units** (lowercase only):
- `m` or `min`: minutes
- `h`: hours

**Examples**:
- `+15m`, `-2h`, `+2h30m`, `-1h15min`

**Base**: Always `now` (current datetime)

**Range constraint**: Total offset must not exceed ±72 hours.

**Forbidden combinations**:
- Relative date + relative offset: `"today +2h"` is NOT allowed
- Use `"+2h"` directly (base is `now`), or `"today 15:00"` (explicit time)

### 4. Time Constraints by Command Type

**Event** (records of things that happened):
- Forbidden: Time later than `now` (for both `--at` and `--new-at`)
- Allowed: Time earlier than `now` (past events)
- Reason: Events represent "things that already happened", cannot be future

**Todo** (tasks to be done):
- Allowed: Any time (past, present, future)
- Reason: Todos can be scheduled for any time

### 5. Edit Command: `--new-at`

Replace `--new-time` with `--new-at`:
```bash
timeline-cli event edit e123 --new-at "15:00"
timeline-cli todo edit t123 --new-at "today 10:00"
```

**Todo edit conversion**:
- `undated → dated`: `--new-at "today 15:00"` (allowed)
- `dated → undated`: `--new-at ""` (allowed)

**Event edit constraint**:
- `--new-at` must not be later than `now` (same as add)

### 6. Output Format (unchanged from ADR-0010)

| Scenario | Output Format |
|----------|---------------|
| Has date and time | `[id] Added: text (YYYY-MM-DD HH:MM)` |
| Has date, no time | `[id] Added: text (YYYY-MM-DD no-time)` |
| No date (undated) | `[id] Added: text (undated)` |

Output always shows normalized, explicit values. Original input is not preserved.

**Examples**:
```bash
$ timeline-cli todo add "Review PR" --at "+2h"
[txxxx] Added: Review PR (2026-06-22 16:30)

$ timeline-cli todo add "Write tests" --at today
[txxxx] Added: Write tests (2026-06-22 no-time)

$ timeline-cli todo add "Someday task" --at ""
[txxxx] Added: Someday task (undated)

$ timeline-cli event add "Meeting" --at "yesterday 15:00"
[exxxx] Added: Meeting (2026-06-21 15:00)
```

## Consequences

### Positive

- **Simplified invocation**: `--at now` replaces `--date today --time now`
- **Unified semantics**: `now` naturally means "current moment" (date + time)
- **Flexible input**: Relative dates, explicit times, and offsets all supported
- **Clear constraints**: Event cannot be future, Todo can be anything
- **Prevents unreasonable offsets**: ±72h limit prevents "100 hours ago" nonsense

### Negative

- **Breaking change**: Users must adapt from `--date`/`--time` to `--at`
- **Complex parsing**: More input formats to handle
- **Potential confusion**: `"today +2h"` is forbidden, users must learn distinction

### Migration

No data migration required. Only affects CLI argument parsing.

**User migration guide**:
```bash
# Old → New
--date today --time now      → --at now
--date today --time 15:00    → --at "today 15:00"  or --at "15:00"
--date 2026-06-22 --time 10  → --at "2026-06-22 10:00"
--date today                 → --at today
--date ?                     → --at ""
```