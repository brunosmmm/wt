---
id: SPEC-0007
title: "`wt agenda` date views"
status: done
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M2: tasks"
kind: feature
tags: [tasks, org, reporting, cli]
parent: SPEC-0004
depends_on: [SPEC-0005]
---

## Context

The second v1 must-have of the [SPEC-0004](./0004-org-task-management.md) epic: a **date
view** over tasks driven by `SCHEDULED`/`DEADLINE`, like org-agenda's day/week views, using
the [SPEC-0005](./0005-org-parser-and-task-model.md) `Task` model. (The real files have no
scheduling yet, so this must degrade gracefully to an empty/overdue view.)

## Goals / Non-goals

**Goals**
- `wt agenda` with the standard `date` + `-w/--week` + `--last` scope convention and the
  `"now"` sentinel, showing tasks whose `SCHEDULED`/`DEADLINE` fall in scope.
- An **overdue** section: not-done tasks with a `DEADLINE` before the scope start.

**Non-goals**
- Time joins/digests (SPEC-0008), list/filter (SPEC-0006), or mutation (SPEC-0009).
- Inventing scheduling data; tasks without dates simply don't appear (except overdue).

## Decision

Add `report.agenda(cfg, *, day, week, last)` and a `@cli.command("agenda")` handler mirroring
`report_cmd`'s scope handling. Reuse `report._scope_days(cfg, day, week, last)` to compute the
date list + title. Group in-scope tasks by day; each row shows the relevant date, its kind
(`SCHEDULED`/`DEADLINE`), state, and the (styled) heading. Overdue rendered as a distinct
`Panel` above the day tables.

## Design

### CLI (`src/wt/cli.py`)

```
wt agenda                 today
wt agenda --week          this week
wt agenda 2026-07-20      that day
wt agenda -w 2026-07-20   that week
wt agenda --last 7        last 7 days
```

Positional `date` (default `"now"`), `--week/-w` flag, `--last N`. Delegates to
`report.agenda(cfg, day=..., week=..., last=...)` following `report_cmd`'s branching.

### Rendering (`src/wt/report.py`)

`agenda(...)`:
1. `days, title = _scope_days(cfg, day, week, last)`; `scope = set(days)`.
2. `tasks = org.load_tasks(cfg)`.
3. For each task, collect `(date, kind)` entries where `kind ∈ {SCHEDULED, DEADLINE}` and the
   date's ISO is in `scope`. Group by day.
4. **Overdue:** not-done tasks whose `DEADLINE` ISO `< days[0]`.
5. Render a `Panel` title (like `report`), one `Table` per day with entries (columns: kind,
   state, task), then the overdue `Panel` (red) if any. Empty scope + no overdue ⇒
   `[dim]nothing scheduled in range[/]`.

Deadlines styled with urgency (red), scheduled neutral; reuse existing color conventions and
`_topic_style` for any JIRA-keyed headings.

## Alternatives considered

- **Merge into `wt tasks --agenda`** — rejected; the scope convention (`date`/`-w`/`--last`)
  belongs on its own verb to match `report`/`review`, and the output shape differs.
- **Synthesize SCHEDULED from tracked time** — out of scope; that's the SPEC-0008 join, not an
  agenda-date source.

## Acceptance criteria

- [x] `wt agenda`, `wt agenda --week`, `wt agenda DATE`, `wt agenda -w DATE`, and
      `wt agenda --last N` each resolve scope via `_scope_days` and render.
- [x] Tasks with `SCHEDULED`/`DEADLINE` in scope appear under the right day with the right
      kind label; tasks without dates don't appear (unless overdue).
- [x] Not-done tasks with a `DEADLINE` before scope start show in an **overdue** section.
- [x] Empty scope prints a friendly line, not a traceback.

## Test plan

- **Automated:** fixtures with explicit `SCHEDULED:`/`DEADLINE:` planning lines (added to the
  SPEC-0005 fixture set). Assert the grouping/overdue **selection** logic (a pure function
  over `Task`s + a scope) puts each task in the correct bucket; a done task with a past
  deadline is **not** overdue; a task with no dates is absent. Rendering smoke-tested via a
  captured `console`; CLI via `CliRunner` (exit 0, expected substrings).
- **Manual verification:** `uv run wt agenda --week` against real `~/work/org` (expected: empty
  or overdue-only today, since no scheduling exists yet) — confirms graceful degradation.
- **Regression guard:** `uv run pytest` stays green.

## Rollout / migration

1. Add `SCHEDULED`/`DEADLINE` handling to `Task` selection (dates already parsed in 0005).
2. `report.agenda(...)` + `wt agenda` CLI handler.
3. Tests + manual check; close the loop.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 39 passed;
      `tests/test_agenda.py` + `tests/fixtures/org/planned.org` cover bucketing/overdue/empty +
      CLI); manual `wt agenda --week` against real `~/work/org` → graceful "nothing scheduled".
- [x] No regressions.
- [x] Spec body updated to match what shipped (pure `_agenda_buckets` helper for testability).
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
