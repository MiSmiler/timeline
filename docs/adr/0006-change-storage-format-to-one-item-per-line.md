# ADR 0006: Change Storage Format to One Item Per Line

## Status

Accepted

## Context

The original storage format in `.timelines.jsonl` (previously `timelines.jsonl`) grouped all items by date, with one line representing a complete daily record:

```jsonl
{"schema_version": 1}
{"date": "2025-01-15", "events": [...], "todos": [...], "notes": "..."}
```

This format made it difficult to observe data changes in version control (git diff). When items were added or modified on the same day, the entire line changed, making it hard to see what specifically changed.

Additionally, the file name `timelines.jsonl` did not clearly communicate that this is tool-managed internal data that users should not edit directly.

## Decision

We change the storage format to store one item per line, and rename the file with a dot prefix:

1. **File name**: `timelines.jsonl` → `.timelines.jsonl`
   - Expresses "tool-managed internal data" similar to `.git/`
   - Signals users should not edit directly

2. **Storage format**: One line per item, not per day
   ```jsonl
   {"schema_version": 1}
   {"type": "event", "id": "e4x1m", "date": "2025-01-15", "time": "09:00", "text": "...", "details": []}
   {"type": "todo", "id": "t7b3k", "date": "2025-01-15", "time": "10:00", "text": "...", "status": "pending", "details": []}
   {"type": "note", "date": "2025-01-16", "text": "..."}
   ```

3. **Item type field**: Uses full strings `"event"`, `"todo"`, `"note"` for readability

4. **Undated Todos**: Use `date: null` instead of special date `0000-00-00`

5. **Sort order**: Items sorted by `(date ASC, type ASC, time ASC)`
   - `date`: null (undated) sorts last
   - `type`: event < todo < note
   - `time`: null sorts last within same type

6. **In-memory model**: Keep `DailyRecord` layer for efficient date-based queries; only `to_lines`/`from_lines` change

7. **Schema version**: Remain at 1 (early development stage, no backward compatibility concerns)

## Consequences

**Positive**:
- Git diff shows exactly which items changed, not entire daily records
- File name clearly communicates "internal data, don't edit"
- Each item is independently traceable in version history
- Same-day items grouped by type for easier browsing

**Negative**:
- Slightly larger file size (date repeated per item vs once per day)
- Need to update `to_lines`/`from_lines` in `models.py`
- Doctor validation rules need updating

**Neutral**:
- In-memory model unchanged; only storage layer affected
- Query performance unchanged (Daily Record layer preserved)

## Alternatives Considered

1. **Keep one-line-per-day but add item-level metadata**: Rejected because it doesn't solve the git diff problem
2. **Use abbreviated type field (`e`/`t`/`n`)**: Rejected because full strings are more readable for humans observing data changes
3. **Flatten in-memory model**: Rejected because it would complicate date-based queries and require more code changes