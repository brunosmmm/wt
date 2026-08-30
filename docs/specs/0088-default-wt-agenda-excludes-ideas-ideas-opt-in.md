---
id: SPEC-0088
title: "Default wt agenda excludes ideas (--ideas opt-in)"
status: done
owner: user
created: 2026-07-28
updated: 2026-07-28
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-109
parent: SPEC-0087
tags: [agenda, ideas, workflow]
---

## Context

Child of [SPEC-0087](./0087-workstreams-and-concern-separation-routing.md). `wt agenda` loads
all org tasks with no `is_idea` filter, so a dated idea can appear beside daily TODOs. `wt
tasks` already uses `is_idea=False`. Dispositions (IDEA-109): `--ideas` = tasks∪ideas; done /
terminal dated ideas show like tasks when opted in; filter in `agenda()` before
`_agenda_buckets`.

## Goals / Non-goals

**Goals**
- Default agenda never lists idea headlines.
- Optional `--ideas` includes dated ideas alongside tasks.

**Non-goals**
- Idea capture `--scheduled` / `--deadline` CLI.
- Changing `_agenda_buckets` date logic or agenda styling.
- Ideas-only mode for `--ideas`.

## Decision

In `agenda()`, before `_agenda_buckets`, default to `filter_tasks(load_tasks(cfg),
is_idea=False)`. With `--ideas`, pass the full `load_tasks` list (union). Keep
`_agenda_buckets` pure. Wire `--ideas` on `agenda_cmd`.

## Design

- `report.agenda(..., include_ideas=False)` — filter then bucket.
- `cli.agenda_cmd` — `--ideas` flag → `include_ideas=True`.
- Done/terminal ideas with in-scope dates appear only when `--ideas` is set (same date rules
  as tasks; overdue still skips `is_done`).

## Alternatives considered

- **Filter inside `_agenda_buckets`** — rejected; keep helper date-pure (disposition 3A).
- **`--ideas` = ideas-only** — rejected (disposition 1A = union).

## Acceptance criteria

- [x] Default `wt agenda` never prints an `is_idea` headline (scheduled or overdue).
- [x] `wt agenda --ideas` can show dated ideas alongside tasks.
- [x] `_agenda_buckets` signature/behavior unchanged aside from receiving a pre-filtered list.
- [x] Existing `test_agenda.py` cases stay green; new idea-exclusion cases pass.

## Test plan

- **Automated:** extend `tests/test_agenda.py` with tmp ideas+tasks org: default hides dated
  IDEA; `--ideas` shows it; overdue open idea absent by default, present with `--ideas`.
- **Manual:** `uv run wt agenda --week` on live corpus (no surprise ideas).
- **Manual/CI:** Performed 2026-07-28 — targeted pytest green.
- **Regression:** `uv run pytest tests/test_agenda.py`.

## Rollout / migration

None. Behavior change is the fix.

## Definition of done

- [x] AC met; tests pass; ledger updated; spec reflects shipped code.

## Open questions

(none — IDEA-109 dispositions locked)
