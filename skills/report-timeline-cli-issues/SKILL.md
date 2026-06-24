---
name: report-timeline-cli-issues
description: Report issues to the timeline GitHub repo (MiSmiler/timeline). Use this skill when you encounter bugs or design problems while using timeline-cli (via /timeline skill or direct CLI commands) that are NOT caused by your own parameter errors. Must confirm with user before submitting. Requires GitHub CLI (gh) installed and authenticated.
---

# Report Timeline CLI Issues

Report bugs or design problems encountered while using timeline-cli to the GitHub repository.

---

## Prerequisites

Before using this skill, verify that GitHub CLI is available:

```bash
# Check if gh is installed
gh --version

# Check if gh is authenticated
gh auth status
```

If `gh` is not installed, inform the user to install it first: https://cli.github.com/

If `gh` is not authenticated, inform the user to run `gh auth login`.

---

## When to Use This Skill

Use this skill when:

- **Bug**: timeline-cli crashes, throws unexpected errors, or behaves incorrectly
- **Design problem**: The CLI's behavior is confusing, inconsistent, or causes difficulty in normal use

**Do NOT use this skill when**:

- The error is caused by your own parameter mistake (wrong ID format, missing required args, etc.)
- The issue is environment-specific (missing Python, wrong Python version, etc.)

---

## Issue Content Structure

Prepare the following information before creating an issue:

### Required Fields

1. **Title**: Brief, descriptive summary of the problem
2. **Problem Description**:
   - Expected behavior
   - Actual behavior
3. **Reproduction Steps**: The exact command(s) or operations that triggered the problem
4. **Error Output**: Full error message or stack trace (if applicable)
5. **Context**: What task you were helping the user with when the problem occurred

### Optional Fields

6. **Environment Info**:
   - Python version (if obtainable)
   - OS (if known)

---

## Confirmation Workflow

**ALWAYS confirm with the user before submitting.**

1. Prepare the issue content
2. Present it to the user for review:
   - Title
   - Full body (description, steps, error, context)
   - Label: `reported-by-skill`
   - Target repo: `MiSmiler/timeline`
3. Wait for user response:
   - **Confirm** → Submit the issue
   - **Modify** → Update content and re-confirm
   - **Reject** → Cancel submission

---

## Submitting the Issue

After user confirmation, use `gh issue create`:

```bash
gh issue create \
  --repo MiSmiler/timeline \
  --title "TITLE" \
  --body "BODY" \
  --label "reported-by-skill"
```

The `--body` should contain the full issue content formatted in markdown.

---

## Example

**Scenario**: Agent runs `timeline-cli todo list --at today --json` and gets an unexpected error.

**Title**: `todo list --json fails with "Invalid JSON structure"`

**Body**:
```markdown
## Expected Behavior

The command should return valid JSONlines output listing today's todos.

## Actual Behavior

The command throws an error: "Invalid JSON structure at line 3"

## Reproduction Steps

1. Initialize timeline-cli storage: `timeline-cli init`
2. Add a todo: `timeline-cli todo add "Test task" --at today`
3. Run: `timeline-cli todo list --at today --json`

## Error Output

```
Error: Invalid JSON structure at line 3
File: .timeline/data.jsonl
```

## Context

Agent was helping user list today's todos for task planning.
```

After presenting this to the user and receiving confirmation, submit via `gh issue create`.