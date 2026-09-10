---
id: SPEC-0006
title: "`wt tasks` list & filter"
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

With the [SPEC-0005](./0005-org-parser-and-task-model.md) `Task` model in place, the first
v1 must-have is a way to **see and filter** tasks from the terminal — the org equivalent of
`wt topics`. Part of the [SPEC-0004](./0004-org-task-management.md) epic.

## Goals / Non-goals

**Goals**
- `wt tasks` command listing open tasks by default, with filters for state, tag, project,
  and priority, plus flags to include done tasks and to select a source facet.
- A rich table mirroring the `topics()` 4-column shape, using `_topic_style` for JIRA keys.

**Non-goals**
- Date/agenda views (SPEC-0007) or time joins/digests (SPEC-0008).
- Mutating task state (SPEC-0009).

## Decision

Add `report.tasks(cfg, *, state, tag, project, priority, all_done, key)` and a
`@cli.command("tasks")` handler with `@click.pass_obj`. Default view = **open, actionable**
tasks, sorted by (is_done, priority, project, heading). Filters compose (AND). `--all`
includes done tasks.

**Refinement (during implementation):** the SPEC-0005 model faithfully turns *every* headline
into a `Task`, including structural category headings with `state = None` (e.g. "Active
Projects"). Listing those as "open tasks" is noise, so the default view is narrowed to
**actionable** items = tasks that have a TODO `state` **and** are not done. `--all` restores
the full set (done + stateless structural headings). This is more useful and matches how
org-agenda surfaces TODO-keyword items.

## Design

### CLI (`src/wt/cli.py`)

```
wt tasks                      open tasks, all sources
wt tasks --state INPROGRESS   only that TODO state
wt tasks --tag example           tasks tagged example (grouped tags already split)
wt tasks --project Example       tasks under that project/category
wt tasks --priority A         only [#A]
wt tasks --all                include DONE/CANCELED/etc.
wt tasks --key                only tasks with a topic_key (JIRA-linked)
```

Options: `--state`, `--tag`, `--project`, `--priority` (all optional strings),
`--all/all_done` (flag), `--key` (flag). Delegates to `report.tasks(...)`.

### Rendering (`src/wt/report.py`)

`tasks(...)` calls `org.load_tasks(cfg)`, applies `org.filter_tasks(...)` (done-filtering via
`all_done`, plus `--key` ⇒ `topic_key is not None`), then renders a `Table`
(`box.SIMPLE_HEAVY`, `header_style="dim"`, `pad_edge=False`) with columns: **state**,
**pri**, **task** (heading, JIRA key styled via `_topic_style(topic_key)` when present),
**project · tags**. Empty result prints `[dim]no matching tasks[/]`. A `Panel` header echoes
the active scope/filters and total count (matching the `topics()` header style).

State coloring: done states dim, `INPROGRESS`/active states highlighted; reuse existing
palette conventions (no new color module).

## Alternatives considered

- **Fold tasks into `wt topics`** — rejected; topics are time-derived base keys, tasks are
  org-derived; separate verbs keep each table honest.
- **JSON/CSV output now** — deferred; export can piggyback on SPEC-0008's tidy-dataset work
  if wanted. v1 is terminal-first.

## Acceptance criteria

- [x] `wt tasks` lists open, actionable tasks from the configured sources; done + structural
      headings hidden by default (shown under `--all`).
- [x] `--state`, `--tag`, `--project`, `--priority`, `--key`, and `--all` each filter as
      documented and compose (AND).
- [x] JIRA-keyed tasks render with the JIRA style; the table matches the `topics()` shape.
- [x] No matches prints a friendly empty-state line, not a traceback.

## Test plan

- **Automated:** `tests/test_org.py` (or `test_tasks.py`) drives `report.filter_tasks`/the
  selection logic over SPEC-0005 fixtures: assert default hides done, each filter narrows
  correctly, filters compose, and `--key` keeps only `topic_key`-bearing tasks. Rendering is
  smoke-tested by invoking `report.tasks` with a captured `console` (no exception; expected
  rows present). CLI wired via `click.testing.CliRunner` asserting exit 0 and key substrings.
- **Manual verification:** `uv run wt tasks`, `uv run wt tasks --state INPROGRESS`,
  `uv run wt tasks --project Example` against real `~/work/org`, eyeballed.
- **Regression guard:** `uv run pytest` stays green; existing commands unaffected.

## Rollout / migration

1. `report.tasks(...)` + reuse of `filter_tasks`.
2. `wt tasks` CLI handler.
3. Tests + manual check; close the loop.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 34 passed; `tests/test_tasks.py`
      covers default/all/state/tag/key/empty + CLI); manual `wt tasks` run against real `~/work/org`.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
