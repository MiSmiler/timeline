# Introduce timeline-cli with jsonline storage

The timeline system originally used markdown files as the source of truth, with SKILL.md defining format and semantics in text. This caused AI agents to occasionally misinterpret operations. We introduce `timeline-cli` to codify semantics as CLI commands, using jsonline as the single source of truth.

## Storage Design

**Decision**: Single `timelines.jsonl` file in project directory.

Alternatives considered:
- Per-day jsonline files: rejected for simpler management and unified version control
- Per-day JSON files: rejected for consistency with jsonline append-friendly nature

Schema version in file header (`{"schema_version": 1}`). Migration is explicit via `timeline-cli migrate --to <version>`, not automatic. This provides control and predictability.

## Data Model

**Decision**: No ID for Todo/Event. Location via date + time (optional) + text prefix matching.

Alternatives considered:
- UUID/short ID: rejected to simplify data structure and reduce query overhead. Agents can match by natural language description.

Time format: `HH:MM` string for timed items, `null` for untimed. Details as array (`[]` for empty). Notes as single string (`null` for empty).

## CLI Design

**Decision**: Resource-first command structure (`timeline-cli todo add`).

Alternatives considered:
- Verb-first (`timeline-cli add todo`): rejected for better grouping and tab-completion.

CLI accepts only `YYYY-MM-DD` dates. Natural language parsing ("today", "tomorrow") is the agent's responsibility, keeping CLI simple.

Query output formats: table (default), `--json`, `--simple`.

## Import/Export

**Decision**: Export is a CLI command. Import is a separate migration script.

Reason: Import is a one-time operation for existing users. Including it in CLI would expose unnecessary complexity. `scripts/migrate_from_markdown.py` handles first-time migration.

Export writes to `--output-dir` with auto-generated filenames (`YYYY-MM-DD.md`), preventing user naming errors.

## SKILL.md Role

**Decision**: SKILL.md guides agents on CLI usage, not direct markdown manipulation.

SKILL.md describes when and how to invoke timeline-cli commands. CLI handles all data operations. This reduces agent interpretation errors while keeping semantic guidance.

## Implementation

- Language: Python
- CLI framework: argparse (standard library, no dependencies)
- Package management: uv
- Linting/formatting: ruff
- Installation: `pip install -e` for development, publishable to PyPI later
- Testing: Unit tests for storage and operations modules

## Concurrency

**Decision**: No concurrency control.

Single user, single agent. If concurrency becomes necessary later, atomic write (write-to-temp + rename) is the preferred approach.