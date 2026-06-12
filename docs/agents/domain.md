# Domain Docs

This repository uses a **single-context** layout.

## Files

- `CONTEXT.md` — Project domain language and concepts (to be created)
- `docs/adr/` — Architecture Decision Records (to be created)

## Consumer Rules

Skills that read domain docs should:

1. Read `CONTEXT.md` at repo root for domain language
2. Read `docs/adr/*.md` for architectural context
3. If `CONTEXT.md` doesn't exist yet, proceed without domain context

## Creating CONTEXT.md

A `CONTEXT.md` should describe:
- Core domain concepts and terminology
- System architecture overview
- Key abstractions and their relationships