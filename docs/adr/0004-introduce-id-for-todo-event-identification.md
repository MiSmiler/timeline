# ADR-0004: Introduce ID for Todo/Event Identification

## Status

Accepted

## Context

Previous design used natural language locating: `date + time (optional) + text_prefix`. This "no ID" approach had several problems:

1. **Ambiguity**: Multiple todos with same prefix (e.g., "学理财：看书" and "学理财：记账") cannot be distinguished by text_prefix alone
2. **Same-time conflicts**: Multiple todos at same time + same date cannot be uniquely identified
3. **Script/Agent unfriendly**: Automated tools need complex logic to handle ambiguous results
4. **Reference instability**: Editing text changes what text_prefix matches

The design philosophy of "natural" interaction turned out to be poor user experience for precise operations.

## Decision

Introduce unique IDs for todos and events:

- **ID format**: Short random ID (5-6 alphanumeric characters)
- **Display format**: Type prefix + ID (`t7b3k` for todo, `e4x1m` for event)
- **Scope**: Separate ID sequences per type (todos and events have independent IDs)
- **Generation**: Assigned at creation time, immutable thereafter
- **Migration**: Existing data gets IDs via `doctor --fix`

## Consequences

### Positive

- Precise, unambiguous identification for all operations
- Script and agent-friendly: single ID reference works reliably
- ID persists across edits/moves (unlike text_prefix)
- Simple user input: 5-6 characters vs full text or UUID

### Negative

- Data model change: adds `id` field to Todo and Event
- Requires migration for existing data
- Breaking change for any existing automation that relied on text_prefix

### Mitigation

- Keep `text_prefix` as optional fallback for human convenience (but recommend ID)
- `doctor --fix` handles migration automatically
- Clear error messages guide users to use `--id` when ambiguous

## Examples

```bash
# List shows ID
timeline-cli todo list
# ID     Date        Time   Status     Text
# t7b3k  2026-06-19  10:00  pending    学理财：看书
# ta2x1  2026-06-19  10:00  pending    学理财：记账

# Precise operation
timeline-cli todo complete --id t7b3k
timeline-cli todo edit --id t7b3k --new-date 2026-06-20 --new-time 15:00
timeline-cli todo edit --id t7b3k --clear-time  # Remove time, make it undated

# Event operations
timeline-cli event edit --id e4x1m --new-text "重要会议"
timeline-cli event delete --id e4x1m
```

## Related Changes

- Remove `todo move` command: merged into `todo edit --new-date`
- `todo edit` now supports: `--new-text`, `--new-date`, `--new-time`, `--clear-time`, `--append-detail`, `--set-detail`
- `event edit` now supports: `--new-text`, `--new-date`, `--new-time`, `--append-detail`, `--set-detail`