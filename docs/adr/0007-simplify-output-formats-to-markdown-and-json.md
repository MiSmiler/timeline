# ADR 0007: Simplify Output Formats to Markdown and JSON

## Status

Accepted

## Context

The CLI had three output formats: `table`, `json`, and `simple`. Additionally, `export` and `export-all` commands generated markdown files to disk.

This created complexity:
- Three formats with overlapping purposes
- `table` format was machine-readable but not human-friendly
- `simple` format was rarely used
- Export commands encouraged users to treat markdown files as source of truth
- `--output` parameter required for every command, adding friction

## Decision

Simplify to two output formats with clear purposes:

1. **Markdown** (default): Human-readable, for users
2. **JSON** (via `--json` flag): Machine-readable, for agents and tools

Changes:
- Remove `table` and `simple` formats
- Remove `export` and `export-all` commands
- Change `--output markdown/json` to `--json` flag (markdown is default)
- Add `--show-id` flag for markdown output (json always includes id)
- Add `diary` command for complete single-day view (markdown only)
- Unify action command output to git-style: `[id] Action: text`
- Support relative date keywords (`today`, `yesterday`, `tomorrow`) in all commands

## Consequences

### Positive
- Clear separation: markdown for humans, json for machines
- Simpler CLI: fewer parameters, clearer defaults
- No markdown file generation: source of truth stays in jsonline
- Unified output style across action commands

### Negative
- Breaking change: users with scripts depending on `export` or `table` format will need updates
- Users who want markdown files must now copy from terminal output

### Mitigation
- Document changes clearly in CHANGELOG
- Provide migration guidance for affected users