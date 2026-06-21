# ADR 0008: Change JSON Output to JSONlines Format

## Status

Accepted

## Context

The CLI's `--json` output currently uses pretty-printed JSON arrays:

```json
[
  {
    "id": "tvbsk0",
    "date": "2026-06-12",
    "time": "17:30",
    "text": "小象买菜",
    "status": "completed",
    "details": []
  },
  {
    "id": "totk77",
    ...
  }
]
```

This format has issues when consumed by AI Agents:
1. **Token overhead**: Indentation and array brackets consume extra tokens
2. **Not stream-friendly**: Entire array must be parsed before processing
3. **Inconsistent with storage**: Storage uses jsonlines, but output uses array JSON

## Decision

Change `--json` output to pure JSONlines format (one JSON object per line, no array wrapper):

```jsonl
{"id": "tvbsk0", "date": "2026-06-12", "time": "17:30", "text": "小象买菜", "status": "completed", "details": []}
{"id": "totk77", "date": "2026-06-12", "time": null, "text": "买摄像头", "status": "abandoned", "details": []}
```

### Scope of Changes

| Command | Before | After |
|---------|--------|-------|
| `todo list --json` | Pretty-printed JSON array | JSONlines |
| `event list --json` | Pretty-printed JSON array | JSONlines |
| `list --json` | Pretty-printed JSON array | **Remove `--json` flag** |
| `todo list` (default) | Markdown | unchanged |
| `event list` (default) | Markdown | unchanged |
| `list` (default) | Markdown with counts | unchanged |

### Design Decisions

1. **Output format**: Pure JSONlines, no array wrapper (follows [jsonlines.org](https://jsonlines.org/) standard)

2. **Empty results**: stdout empty, stderr shows message (e.g., "No todos found")

3. **Null handling**: Keep `null` for empty values (consistent with current behavior)

4. **Chinese characters**: Use `ensure_ascii=False` (consistent with current behavior)

5. **Field order**: `id`, `date`, `time`, `text`, `status`, `details`
   - `id` first for quick reference and subsequent operations (edit, complete, delete)
   - Different from storage format which puts `id` last

6. **Implementation**: Encapsulate JSON serialization in a single utility function to ensure consistent `ensure_ascii=False` usage

### Note on Storage vs Output Format

The storage file `.timelines.jsonl` and CLI JSON output have different field orders:

- **Storage format**: `type`, `date`, `time`, `text`, `details`, `id` — optimized for git diff readability
- **Output format**: `id`, `date`, `time`, `text`, `status`, `details` — optimized for AI Agent operations

This difference is intentional. `.timelines.jsonl` is not meant to be consumed by AI Agents; it serves as a human-readable storage format. AI Agents should always consume CLI output, not raw storage files.

## Consequences

### Positive
- Reduced token consumption for AI Agents (no indentation, no array brackets)
- Stream-friendly: AI can parse line by line
- Consistent with jsonlines standard
- Simpler parsing logic for consumers

### Negative
- Breaking change for scripts relying on current JSON array format
- `list --json` removal affects users who used it

### Mitigation
- Document in CHANGELOG
- No transition period needed (project at 0.x stage, API can change)
- Users primarily self/AI Agents, migration is controlled