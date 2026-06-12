# Timeline

A markdown-based daily event and todo management system. Records daily occurrences with minimal todo management capability. Not designed for long-term goals, recurring tasks, project materials, or periodic reviews.

## Core Concepts

**Todo**:
A task to be done. May have a specific time or be undated. Three states: pending `[ ]`, completed `[x]`, abandoned `[ ] ~~description~~`.
_Avoid_: Task, item, reminder

**Event**:
A record of something that happened at a specific time. Immutable once created.
_Avoid_: Entry, occurrence, log

**Note**:
Free-form text without time constraints. Captures thoughts, goals, or mood.
_Avoid_: Memo, thought

## Files

**Daily File**:
Markdown file named `YYYY-MM-DD.md` in `timelines/` directory. Contains Events, Todos, and Notes sections for that date.
_Avoid_: Day file, date file

**Undated File**:
Special file `0000-00-00.md` in `timelines/`. Only contains Todos without time prefix. Not allowed to have Events or Notes.
_Avoid_: Inbox, backlog file

## Tooling

**Doctor**:
A diagnostic script that validates data format and optionally fixes issues with `--fix` flag. Unfixable problems fall back to AI agent for text-based repair.
_Avoid_: Validator, checker

## Architecture

**timeline skill**:
Platform-agnostic core skill that reads/writes markdown files. Does not depend on specific platform features.

**setup-\* skill**:
Platform-specific deployment skill that handles wrapper scripts, cron integration, and AGENTS.md injection. Examples: `setup-timeline-for-hermes`, `setup-timeline-for-openclaw`.

## Boundaries

Timeline system **does not** manage:
- Long-term goals (e.g., "learn Rust this year")
- Recurring tasks (e.g., "exercise 3 times a week")
- Project materials (e.g., requirement doc links)
- Periodic reviews (e.g., weekly summary)

These belong to other markdown files or future separate skills.