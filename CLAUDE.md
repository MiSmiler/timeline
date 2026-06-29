# Timeline CLI Agent Guide

Guidelines for AI agents working on this project.

## Development Guide

See [README.md](README.md#development) for toolchain, commands, and testing instructions.

## Agent Skills

### Issue Tracker

Issues are tracked in GitHub Issues. Uses `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage Labels

Default label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain Docs

Single-context layout: `CONTEXT.md` and `docs/adr/` at repo root. See `docs/agents/domain.md`.

## Coding Conventions

### Error messages

**Do not include `{exc}` in error messages when using `from exc`.** The exception chain (`from exc`) already preserves the original error details in the traceback — adding `{exc}` to the message string produces duplicate information. For example:

```python
# ❌ Wrong — duplicates OSError details in both message and traceback
raise TimelineError(f"Cannot write {path}: {exc}") from exc

# ✅ Correct — message states what failed; traceback carries the reason
raise TimelineError(f"Cannot write {path}") from exc
```

The **only exception** is when `exc` is a `KeyError` from `from_dict`, where `str(exc)` is the bare field name (e.g. `'start_time'`). In that case it tells the user *which* field is missing, not merely a redundant system detail.