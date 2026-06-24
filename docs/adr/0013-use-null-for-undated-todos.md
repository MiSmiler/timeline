# 0013: Use `date: null` for Undated Todos

## Status

Accepted

## Context

Previously, undated todos were stored with `date: "0000-00-00"` — a magic string value. This approach has several problems:

1. **Semantic confusion**: `"0000-00-00"` is not a real date; it's a placeholder that requires special handling everywhere.
2. **Type inconsistency**: The `date` field is typed as `str`, but `"0000-00-00"` is semantically "no date", not a date string.
3. **Spread of magic value**: The magic string appears in multiple places (storage, commands, output formatter, filter logic), increasing maintenance burden.

## Decision

Change undated todos to use `date: null` in storage and `None` in memory.

**Layer-by-layer representation:**

| Layer | Representation |
|-------|---------------|
| CLI input | `--at undated` (keyword) |
| Storage (JSON) | `date: null` |
| Memory (dict key) | `None` |
| Memory (DailyRecord.date) | `str \| None` |
| Markdown output | `# Undated` |

**TimeExpr design:**

`undated` is treated as a special Timerange keyword (like `today`), with `is_undated: bool` flag in the Timerange class. The filter layer recognizes this flag and matches only items with `date=None`.

**Filter logic:**

Items with `date=None` are not part of the time dimension. They are:
- Included when `--at undated` (only these items)
- Included when `--at ..` (full range, all items)
- Excluded from any concrete Timerange (e.g., `today`, `2026-06-23..2026-06-25`)

**Backward compatibility:**

Strict rejection. If `"0000-00-00"` is read from storage, the system reports an error. No automatic migration. This is acceptable because no user data currently uses this magic value.

## Consequences

- **Type change**: `DailyRecord.date` becomes `str | None`; `dict[str, DailyRecord]` becomes `dict[str | None, DailyRecord]`.
- **Clear semantics**: `null/None` explicitly means "no date", eliminating magic value ambiguity.
- **Consistent sorting**: Items with `date=None` sort last, using `"9999-99-99"` as sort key.
- **Clean output**: Markdown shows `# Undated` for null-date items, not `# null` or `# 0000-00-00`.
- **No backward compatibility**: Users with old data containing `"0000-00-00"` will get an error; they must manually fix or delete the data.