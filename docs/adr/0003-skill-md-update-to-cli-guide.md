# Update SKILL.md to CLI-based Operation Guide

## Context

With timeline-cli introduced (ADR-0002), SKILL.md needs to change from a markdown file manipulation guide to a CLI command usage guide. This ADR documents the design decisions for this update.

## Decisions

### Document Structure

**Positioning**: SKILL.md becomes a hybrid document—operation semantics + reference to data format. Not purely an operation manual.

**Data format location**: Full schema definition goes in `skills/timeline/reference/data-format.md`. SKILL.md references it, doesn't inline it.

**Reference directory**: Contains only `data-format.md`. No cheatsheet or output examples (agents can use `--help`).

**Organization**: Organize by **scenario**, not by command. Example: "Complete Todo" section, not "timeline-cli todo complete" section. Scenarios match agent decision flow: "user says complete → which command?"

### Operation Semantics

**Output format**: Recommend `--json` for **all commands**. Simplifies agent parsing logic uniformly.

**Date handling**: Briefly mention CLI only accepts `YYYY-MM-DD`. Agents handle natural language conversion (today/tomorrow/yesterday).

**Location semantics**:
- Todo/Event: `date + text` **full-text match** (not prefix). Ambiguous matches require `--time` parameter.
- Note: Only `date` needed (one note per date).

**Ambiguity handling**: CLI returns structured error (`ambiguous_match`) with candidate entries. Agent retries with `--time` based on error info.

**Constraints**: Don't mention in SKILL.md. CLI handles validation automatically.

**Recommendations**: Keep recommendations in each scenario but update phrasing. Example: "After completing Todo, optionally call `timeline-cli event add` to record completion time."

**Delete confirmation**: Agent confirms with user first, then calls command with `--yes` parameter.

**Confirmation parameter name**: `--yes` (most intuitive, matches confirmation dialog).

### Content Scope

**Query scripts**: Delete `skills/timeline/scripts/` directory. All querying via CLI commands.

**Doctor**: Don't mention. Advanced feature, not for daily agent use.

**Export**: Briefly mention in "Query & Export" section. Don't expand.

**Init**: Mention in introduction, not a separate section.

**Error handling**: Brief guidance on common error types and agent response strategies.

### SKILL.md Chapter Structure

```
# Introduction
- timeline-cli positioning
- Reference to data-format.md

# Date Handling
- CLI only accepts YYYY-MM-DD

# Operation Semantics
## Todo Operations
### Create Todo
### Complete Todo (with recommendation: create Event)
...

## Event Operations
...

## Note Operations
...

## Query & Export
### List entries
### Export as markdown

# Error Handling
- Common error types + agent strategies
```

## Consequences

- Agents use CLI uniformly, no direct file manipulation
- SKILL.md stays scenario-focused, matches agent decision flow
- Data format reference is separate, keeps SKILL.md concise
- Clear error handling guidance reduces agent confusion
- Deleting scripts simplifies maintenance