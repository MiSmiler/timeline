# ADR-0005: Schema Version 2 and Project Version 0.2.0

## Status

Accepted

## Context

Multiple issues (#36, #37, #38, #39, #40, #41) required changes to CLI API and data model:

1. **ID introduction** (ADR-0004): Todo/Event need unique identifiers for precise operations
2. **UTF-8 encoding**: JSONL files should store Chinese characters directly, not Unicode escapes
3. **CLI API redesign**: Unified `--range`, `--output`, `--contains` parameters; removed `move` command

These changes affect:
- Data model (new `id` field)
- File format (encoding)
- CLI interface (breaking changes)

## Decision

### Schema Version Upgrade

Upgrade schema version from 1 to 2. Migration (`migrate --to 2`) performs:

1. **Assign IDs**: Generate unique IDs for all existing Todo/Event records
2. **Reencode to UTF-8**: Rewrite file with `ensure_ascii=False` for readable Chinese characters

### Project Version Upgrade

Upgrade project version from `0.1.0` to `0.2.0`.

Breaking changes:
- Removed `todo move` command (use `todo edit --new-date`)
- Changed `todo add` / `event add` parameter order: text positional first
- Removed `--json` / `--simple` flags (use `--output json/simple`)
- Removed `--overdue` / `--undated` flags (use `--range`)
- Removed positional `date` from `event list` (use `--range`)
- Changed `todo edit` / `event edit` to require `--id`

New features:
- ID-based identification for Todo/Event
- `--range` parameter for time filtering (required for list commands)
- `--output` parameter for output format control
- `--contains` parameter for substring matching
- `--clear-time` for removing todo time
- `today` / `now` keywords in range syntax

## Consequences

### Positive

- Consistent, predictable CLI API
- Script/agent-friendly operations with IDs
- Human-readable JSONL files
- Clear migration path for existing data

### Negative

- Breaking changes require users to update scripts/workflows
- Existing data must be migrated
- Agent skills documentation may need updates

### Migration Guide

```bash
# Upgrade schema
timeline-cli migrate --to 2

# New CLI usage examples
timeline-cli todo add "学理财" --date 2026-06-19 --time 10:00
timeline-cli todo list --range today --output json
timeline-cli todo edit --id t7b3k --new-time 15:00 --clear-time
timeline-cli event add "开会" --date 2026-06-19 --time 09:00
timeline-cli event list --range 2026-06-01..2026-06-17
```