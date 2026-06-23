# 11. Timeline Directory Structure

## Status

Accepted

## Context

The current storage uses a single `.timelines.jsonl` file in the working directory. This design has limitations:

1. **Single file constraint**: Cannot naturally accommodate additional files (locks, backups, multiple data files).
2. **Flat structure**: No separation between data and potential future configuration.

## Decision

### Directory-based storage: `.timeline/`

Replace single `.timelines.jsonl` file with `.timeline/` directory containing the data file.

**File structure**:
```
.timeline/
└── data.jsonl      # Required: schema header + items
```

**Rationale**:
- Directory structure allows future expansion (multiple data files, locks, caches, config)
- Follows industry conventions (`.git/`, `.cargo/`, `.venv/` are all singular)
- Separates data from potential future configuration cleanly

### Data file: `data.jsonl`

**Requirements**:
- Must exist for CLI to function
- Must contain `schema_version` header (currently always `1`)
- Same format as existing `.timelines.jsonl` (one item per line)

**CLI checks**: If `.timeline/data.jsonl` missing, error: `No timeline found. Run 'timeline-cli init' to initialize.`

### `init` command behavior

| Command | `data.jsonl` | Action |
|---------|--------------|--------|
| `init` | Missing | Create `data.jsonl` (empty schema header) |
| `init` | Exists | Error: `Timeline already initialized` |

**Output on success**:
- `Created .timeline/data.jsonl`

## Consequences

### Positive

- **Extensible**: Directory allows future files without schema changes
- **Standard conventions**: `.timeline/` matches `.git/`, `.cargo/` patterns
- **Clean path**: `.timeline/data.jsonl` is clearer than `.timelines.jsonl`

### Negative

- **Migration required**: Users must move `.timelines.jsonl` to `.timeline/data.jsonl`
- **Breaking change**: All commands now expect `.timeline/data.jsonl` path

### Migration

**Manual migration** (user responsibility):
```bash
mkdir .timeline
mv .timelines.jsonl .timeline/data.jsonl
```

**CLI does not auto-migrate**. Single-user project assumption: developer handles migration themselves.

## Related

- ADR-0002: Original jsonline storage decision
- ADR-0006: Per-item storage format
- CONTEXT.md: Updated storage terminology (Timeline Directory, Data File)