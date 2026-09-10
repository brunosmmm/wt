# Hub

Read-only **union triage**: open ideas, active internal specs, outbound outbox, plus a
tasks slice for today.

## When to use

Agent or human “what’s in flight?” without opening three lists. Never writes the ledger.

## Commands

```bash
wt hub --json                     # wt.hub.v1 (+ today tasks by default)
wt hub --json --project P         # filter ideas + today
wt hub --json --tasks-slice open  # capped open actionable tasks
wt hub --json --tasks-slice none  # ideas/specs only
wt hub --json --state TODO        # filter by state
```

![hub --json](../assets/captures/cli-hub.svg)

`--json` is required in v1. Pair with [Ideas & next](ideas.md), [Skills](skills.md)
(`/wt-orient`), and the [Daily](../guides/daily-ops.md) / [Weekly](../guides/weekly-ops.md) ops guides.
