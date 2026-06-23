# PRD: Unified Time Expression System for List Commands

## Problem Statement

The current parameter system for `todo list` and `event list` has several usability issues:

1. **`--range` is required for every invocation** - Users must specify a range even for common cases like "today", making the CLI verbose and tiresome to use.
2. **`--range` syntax is unintuitive** - The `..` separator and `?` for undated todos are symbols that users don't naturally think of.
3. **`--time` parameter is ambiguous** - Only exists for `todo list`, and its semantics are unclear (filter by time point vs. time range).
4. **Todo and Event have inconsistent parameters** - `todo list` has `--time` and `--status`, but `event list` lacks these, creating confusion.
5. **Duplicate parsing logic** - Todo and Event commands each implement their own time parsing, leading to code duplication and potential inconsistency.

## Solution

Introduce a unified **TimeExpr** abstraction that replaces `--range` and `--time` with a single `--at` parameter. This creates a consistent, intuitive time expression system shared across all commands.

Key improvements:
- Single `--at` parameter handles both time points and ranges
- Natural syntax using `T` separator (ISO 8601 inspired) for date+time combinations
- Clear keywords: `undated` replaces `?`, `now` for current timestamp
- `--no-time` filter for todos without time component
- Shared parsing layer eliminates duplication

## User Stories

1. As a CLI user, I want to list today's todos with a simple command, so that I can quickly check my daily tasks without typing verbose parameters.
2. As a CLI user, I want to list todos from a date range using natural syntax, so that I can query historical or future tasks intuitively.
3. As a CLI user, I want to filter todos by exact time point, so that I can find todos scheduled for a specific moment.
4. As a CLI user, I want to list todos without a time component, so that I can see all day-long or undated tasks separately.
5. As a CLI user, I want to use consistent syntax across todo and event commands, so that I don't need to remember different parameter sets.
6. As a CLI user, I want to create undated todos with a clear keyword, so that I don't need to guess what symbol means "no date".
7. As a CLI user, I want to create todos with only time (no explicit date), so that I can quickly add tasks for today.
8. As a CLI user, I want the system to reject invalid time ranges (reversed), so that I don't accidentally create nonsensical queries.
9. As a CLI user, I want `event add` to require a time component, so that events always have precise timestamps as designed.
10. As a CLI user, I want `event list --at undated` to error clearly, so that I understand events must have dates.
11. As a CLI user, I want to filter todos by status across all dates, so that I can review all pending or completed tasks.
12. As a CLI user, I want to search todos by text across all dates, so that I can find tasks containing specific keywords.
13. As a CLI user, I want to combine time filters with status filters, so that I can narrow down results precisely.
14. As a CLI user, I want to use relative keywords like `today`, `yesterday`, `tomorrow`, so that I don't need to calculate dates manually.
15. As a CLI user, I want to combine relative keywords with time, so that I can express "today at 9:00" naturally.
16. As a CLI user, I want to use `now` for current timestamp, so that I can add events/todos at the exact current moment.
17. As a CLI user, I want to list all todos across all dates with `--at ..`, so that I can see my complete task history.
18. As a CLI user, I want the system to enforce at least one parameter on list commands, so that I don't accidentally output massive data and waste tokens.
19. As a developer, I want a single TimeExpr parsing module, so that I don't duplicate logic between todo and event commands.
20. As a developer, I want clear interfaces for Timepoint and Timerange, so that I can extend the system predictably.

## Implementation Decisions

### TimeExpr Abstraction

Introduce `TimeExpr` as the unified time expression abstraction. Contains either a `Timepoint` or a `Timerange`.

```python
class TimeExpr:
    kind: "timepoint" | "timerange"
    # timepoint fields
    date: Optional[str]  # YYYY-MM-DD or None
    time: Optional[str]  # HH:MM or None
    is_undated: bool     # True for undated keyword
    is_now: bool         # True for now keyword
    # timerange fields
    left: Timepoint      # start boundary
    right: Timepoint     # end boundary
```

### Timepoint Components

A Timepoint can have various component combinations:

| Components | Example | Behavior in List Commands | Behavior in Add/Edit Commands |
|------------|---------|---------------------------|------------------------------|
| date + time | `2026-06-23T09:00` | Exact time match | Set precise datetime |
| date + time | `todayT09:00` | Exact time match | Set precise datetime |
| date only | `2026-06-23` | Full day range | Set date, no time |
| date only | `today` | Full day range | Set date=today, no time |
| time only | `09:00` | Auto-fill date=today, exact match | Auto-fill date=today |
| empty | (boundary) | Start/end of all time | Not applicable |
| `undated` | - | Filter undated todos | Create undated todo |
| `now` | - | Current timestamp | Set current datetime |

### Timerange Syntax

Timerange format: `timepoint..timepoint`

Expansion rules applied during parsing:
- Left timepoint has date only → expand to `dateT00:00`
- Right timepoint has date only → expand to `dateT23:59`
- Timepoint has time only → auto-fill date=today
- Empty timepoint → represents start/end boundary

Constraint: `left < right` (reversed ranges raise validation error).

Example expansions:
- `2026-06-23..2026-06-25` → `2026-06-23T00:00..2026-06-25T23:59`
- `today..tomorrow` → `todayT00:00..tomorrowT23:59`
- `09:00..17:00` → `todayT09:00..todayT17:00`
- `..` → start boundary..end boundary (all time)
- `2026-06-23..` → `2026-06-23T00:00..end boundary`

### `T` Separator for Date+Time

Adopt `T` separator (ISO 8601 inspired) to connect date and time components:
- `2026-06-23T09:00` - explicit date + time
- `todayT09:00` - relative keyword + time

This provides a clear, unambiguous syntax that users can recognize from ISO 8601.

### `--at` Parameter

Replace `--range` and `--time` with unified `--at` parameter:
- Accepts Timepoint or Timerange
- For list commands: expands date-only Timepoint to full-day Timerange
- For add/edit commands: Timepoint sets exact or partial datetime

### `--no-time` Parameter

New filter parameter for todos without time component:
- Only valid for Todo commands (Event always has time)
- Can combine with `--at`, but requires `--at` to be Timerange (not Timepoint)
- When used alone, implies default range `..` (all dates)

Semantic: a todo without time "belongs" to any point in its date, so it matches any timerange that includes that date.

### Existing Parameters Retained

- `--status`: Filter by todo status (pending/completed/abandoned). Todo only.
- `--contains`: Filter by text substring (matches text or details). Todo and Event.
- `--json`: Output as JSONlines format. Todo and Event.
- `--show-id`: Display item IDs in markdown output. Todo and Event.

### Execution Rules

1. **Parameter requirement**: `todo list` and `event list` must have at least one parameter (`--at`, `--no-time`, `--status`, or `--contains`). No parameterless invocation allowed.

2. **Default time range**: If no time-related parameter (`--at` or `--no-time`) is specified, default range is `..` (all dates).

3. **Event time requirement**: `event add` and `event edit` require Timepoint with time component. Date-only Timepoint rejected.

4. **Undated rejection for Event**: `event list --at undated` and `event add --at undated` raise validation errors.

### Command-Specific Behavior

| Command | Date-only Timepoint | Time-only Timepoint | `undated` | `now` |
|---------|---------------------|---------------------|-----------|-------|
| `todo list` | Expand to full day | Auto-fill date, exact match | Filter undated | Current time |
| `todo add/edit` | Set date, no time | Auto-fill date, set time | Create undated | Set current |
| `event list` | Expand to full day | Auto-fill date, exact match | Error | Current time |
| `event add/edit` | Error | Auto-fill date, set time | Error | Set current |

### Migration Path

- `--range X` → `--at X` (same syntax for ranges)
- `--range ?` → `--at undated` (keyword replaces symbol)
- `--time HH:MM` → `--at HH:MM` (time-only syntax)
- `event add --at date` → `event add --at dateTHH:MM` (must add time)

### Module Changes

- **New module**: `time_expr.py` - TimeExpr, Timepoint, Timerange parsing and validation
- **Modified**: `cli.py` - Replace `--range` with `--at`, add `--no-time`
- **Modified**: `commands/todo.py` - Use TimeExpr for list/add/edit
- **Modified**: `commands/event.py` - Use TimeExpr for list/add/edit
- **Deprecated**: `range_parser.py` - Functionality moved to `time_expr.py`

## Testing Decisions

### Test Philosophy

Tests focus on external CLI behavior, not implementation details. Each test verifies user-visible outcomes through command execution.

### Test Seams

Using existing test files (no new test layers needed):

- **`test_at_parameter.py`** → Unit tests for TimeExpr parsing functions
  - Test Timepoint parsing with all component combinations
  - Test Timerange parsing and expansion rules
  - Test validation (reversed ranges, Event-specific limits)

- **`test_range.py`** → CLI tests for `--at` parameter behavior
  - Rename to `test_time_expr.py` or extend existing file
  - Test `todo list --at` with various TimeExpr forms
  - Test `event list --at` with various TimeExpr forms
  - Test error cases (undated for Event, reversed ranges)

- **`test_todo.py`** → CLI tests for todo commands
  - Test `todo list --no-time` behavior
  - Test `todo add --at undated` creates undated todo
  - Test `todo add --at HH:MM` auto-fills date
  - Test parameter requirement enforcement

- **`test_event.py`** → CLI tests for event commands
  - Test `event add --at date` rejection (needs time)
  - Test `event add --at undated` rejection
  - Test `event list --at undated` rejection

### Prior Art

Existing tests follow these patterns:
- Use `tempfile.TemporaryDirectory` for isolated storage
- Use `run_cli()` helper from `conftest.py`
- Verify storage file content directly for add/edit commands
- Verify stdout output for list commands
- Mock `date.today()` and `datetime.now()` for relative keywords

## Out of Scope

- Natural language date parsing (e.g., "next Monday", "in two weeks")
- Timezone support (all times assumed local)
- Calendar views or graphical interfaces
- Recurring events/todos
- Bulk operations on multiple items
- Performance optimization for large datasets

## Further Notes

### Design Rationale

The `T` separator choice was deliberate:
- Familiar from ISO 8601, reducing learning curve
- Unambiguous (no conflict with `-` used in dates)
- Clear boundary between date and time parts

The "parameter requirement" rule prevents accidental massive output:
- Users might run `todo list` expecting "today"
- Without requirement, defaulting to `..` (all dates) could output thousands of items
- Explicit parameter ensures user intention

The "time-only auto-fills today" semantics:
- Matches user mental model: "I want a task for 9:00" implies today
- Reduces verbosity for common quick-entry cases
- Consistent with existing behavior in many time-entry systems

### ADR Reference

See ADR-0012 for full design rationale and decision history.

### Glossary Updates

CONTEXT.md has been updated with new terminology:
- **TimeExpr**: Unified time expression abstraction
- **Timepoint**: A point in time with optional components
- **Timerange**: A range between two Timepoints
- **--at**: Unified time filter/spec parameter
- **--no-time**: Filter for todos without time component