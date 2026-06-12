# Triage Labels

The `triage` skill uses these labels to manage issue state:

| Label | Purpose |
|-------|---------|
| `needs-triage` | Maintainer needs to evaluate |
| `needs-info` | Waiting on reporter for more information |
| `ready-for-agent` | Fully specified, AFK-ready (an agent can pick it up with no human context) |
| `ready-for-human` | Needs human implementation |
| `wontfix` | Will not be actioned |

## State Transitions

1. New issue → `needs-triage`
2. After evaluation:
   - Missing info → `needs-info`
   - Ready for agent → `ready-for-agent`
   - Ready for human → `ready-for-human`
   - Won't fix → `wontfix`