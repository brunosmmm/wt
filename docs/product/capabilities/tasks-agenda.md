# Tasks & agenda

Org **actionable** work (distinct from idea seeds).

## When to use

Concrete TODOs with states, tags, schedule; morning agenda; marking done after generate.

## Commands

| Command | Role |
|---------|------|
| `wt tasks` | List open actionable tasks; filters `--state`, `--tag`, `--project`, … |
| `wt agenda` | SCHEDULED/DEADLINE over a date scope + overdue |
| `wt add TEXT` | Capture a new task into the capture file |
| `wt done SELECTOR` | Mark done |
| `wt state SELECTOR STATE` | Set TODO state |
| `wt digest` | Hours joined to tasks by JIRA key (also under [Report](report.md)) |

![agenda](../assets/captures/cli-agenda.svg)

![tasks](../assets/captures/cli-tasks.svg)

Selectors: `:ID:`, `file:line`, JIRA key, or heading substring. Ideas vs tasks: prefer
`wt idea` for seeds and `wt add` for actionable lines — see [Idea → ship](../guides/idea-to-ship.md)
and [Daily ops](../guides/daily-ops.md).
