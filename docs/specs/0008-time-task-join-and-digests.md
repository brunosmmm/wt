---
id: SPEC-0008
title: Time→task join & digests
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

The strategic payoff of the [SPEC-0004](./0004-org-task-management.md) epic: `wt` already
tracks time per **base topic** (JIRA key / repo / …), and org tasks carry the same JIRA keys
as `Task.topic_key` ([SPEC-0005](./0005-org-parser-and-task-model.md)). Joining the two gives
**hours per task/project with zero manual clocking**, plus a **digest** combining status +
tracked time — the differentiator over plain time tracking.

## Goals / Non-goals

**Goals**
- Join tracked time (`aggregate.assemble(cfg)` → `data[day]["topics"]`) to tasks by
  `topic_key`, over the standard date scope.
- `wt digest` (daily/weekly) combining, per task/project: TODO state + tracked hours in scope,
  and surfacing tracked topics with **no** matching task (untracked-in-org) and tasks with no
  tracked time.

**Non-goals**
- Mutation (SPEC-0009). Agenda (SPEC-0007) and list (SPEC-0006).
- Inventing time; hours come only from what `wt` already tracked.

## Decision

Add a join helper in `src/wt/org.py` (or a small `report` helper) mapping `topic_key →
Task`, and `report.digest(cfg, *, day, week, last, by)` rendering the combined view. Time is
summed from `aggregate.assemble(cfg)` restricted to `_scope_days`. Grouping by project reuses
the `_regroup`/facet idea but keyed on `Task.project`/`topic_key` rather than `mappings.yaml`.

## Design

### Join

- `data, _ = assemble(cfg)`; for each day in scope, `data[day]["topics"]` is
  `{base_topic: secs}`. Base topics may be JIRA keys, `repo`, or `repo:branch`. Match a topic
  to a task when `base_topic` (or its `KEY_RE` match) equals a task's `topic_key`.
- Build `hours_by_key: dict[str, float]` (seconds) summed over scope; then
  `task_hours: dict[Task, float]` via the `topic_key → Task` map (a key may map to multiple
  tasks across files — attribute to each; note the ambiguity in output). Topics that match no
  task collect under an **"untracked in org"** bucket.

### Rendering (`src/wt/report.py`)

`digest(...)`:
- Scope + title via `_scope_days`.
- **By task** (default) or **by project** (`--by project`, summing task hours per
  `Task.project`). Table columns mirror `topics()`: hours, share bar (`_bar`), task/project,
  state. JIRA keys styled via `_topic_style`.
- Two follow-on `Panel`s: **untracked-in-org** (tracked topics with no task — candidates to
  add to org) and **no tracked time** (in-scope open tasks with 0 hours).
- The join sanity invariant: `sum(hours_by_key matching a single key) == that key's hours in
  wt report` for the same scope (used as the epic integration check).

### CLI (`src/wt/cli.py`)

```
wt digest                 today: tasks + tracked hours
wt digest --week          this week
wt digest -w DATE         that week
wt digest --last 7        last 7 days
wt digest --by project    group by task project
```

Positional `date`, `--week/-w`, `--last`, `--by`, `@click.pass_obj`.

## Alternatives considered

- **Task as a first-class facet axis in `mappings.yaml`** — rejected as the primary path;
  the join is *derived* from `topic_key`, not hand-mapped. (`--by project` still reuses the
  regroup pattern conceptually.)
- **New clock storage** — rejected; the whole point is zero manual clocking, reusing existing
  tracked time.

## Acceptance criteria

- [x] `wt digest` joins tracked hours to tasks by `topic_key` over the scope and renders
      hours per task; `--by project` groups by `Task.project`.
- [x] For a JIRA-keyed task, its joined hours **equal** that topic's hours in `wt report` for
      the same scope (the epic integration invariant — verified: DEMO-100 = 14.0976h both ways).
- [x] Tracked topics with no matching task appear in an "untracked in org" section; open
      JIRA-linked tasks with no tracked time appear in a "no tracked time" section.
- [x] Scope flags (`date`/`-w`/`--last`) behave like `wt report`.

## Test plan

- **Automated:** `tests/test_join.py` builds a synthetic `assemble`-shaped `data` dict (or
  monkeypatches `assemble`) with known per-topic seconds + SPEC-0005 fixture tasks; asserts
  `hours_by_key`, the `topic_key → Task` mapping (incl. a key matching multiple tasks), the
  untracked/no-time buckets, and the **join invariant** (a key's summed join hours == the
  same key's total in `data` for the scope). Rendering smoke-tested with a captured `console`;
  CLI via `CliRunner`.
- **Manual verification:** `uv run wt digest --week` against real data + `~/work/org`; pick a
  JIRA-keyed task and confirm its hours match `uv run wt report -w` for that key/scope.
- **Regression guard:** `uv run pytest` stays green; `assemble` untouched.

## Rollout / migration

1. Join helper (`topic_key → Task`, `hours_by_key`).
2. `report.digest(...)` + `wt digest` CLI handler.
3. Tests (incl. the invariant) + manual check; close the loop.

**What shipped / deviations:**
- Join lives in `org.join_time(tasks, topic_secs)` (pure/testable) returning
  `(hours_by_key, key_to_tasks, untracked)`; `report._scope_topic_secs` sums
  `assemble()` over the scope (MEETINGS excluded — it can't map to an org task).
- A base topic matches a task by exact `topic_key` **or** its embedded `KEY_RE` key (so a
  `repo:BRANCH-with-KEY` topic still joins).
- The "no tracked time" panel is limited to **open, JIRA-linked** tasks with 0h (the useful
  signal), not every dateless task.
- Verified against real tracked data by pointing a temp org file's task at the tracked key
  `DEMO-100`: join hours == `assemble` hours (14.0976h), confirming the invariant.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 46 passed; `tests/test_join.py`
      covers mapping, invariant, embedded-key, multi-task, digest render + CLI); manual invariant
      check performed on real data.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
