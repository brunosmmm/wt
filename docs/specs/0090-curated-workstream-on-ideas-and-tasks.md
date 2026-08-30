---
id: SPEC-0090
title: "Curated :WORKSTREAM: on ideas and tasks"
status: done
owner: user
created: 2026-07-28
updated: 2026-07-28
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-108
parent: SPEC-0087
tags: [ideas, tasks, workstream, cli]
---

## Context

Child of [SPEC-0087](./0087-workstreams-and-concern-separation-routing.md). Need a lane
orthogonal to `:KIND:` (shape) and `:PROJECT:` (association/routing). Dispositions
(IDEA-108): config `workstreams:` list; hard-fail unknown on write; default `[]`; tasks
capture-time only; ideas get `wt idea workstream --set`. Do not overload project
`AI-workstreams`.

## Goals / Non-goals

**Goals**
- Single-valued `:WORKSTREAM:` on ideas and tasks from a curated config enum.
- `--workstream` on `wt idea` / `wt add` capture and on `wt ideas` / `wt tasks` filters.
- `wt idea workstream --set` mutator for ideas.

**Non-goals**
- Free-form values; tags-as-streams; task post-capture mutator in v1.
- Task JSON (hub child); changing project/kind semantics.

## Decision

- SoT: `DEFAULT_CONFIG["workstreams"] = []` (user replaces via config.yaml).
- Write path: `normalize_workstream(cfg, value)` hard-fails if missing/not in list; writes
  `:WORKSTREAM:` via capture drawer / `set_property`.
- Read of stale unknown values: still surface in show/JSON; filters/`Choice`/completers only
  offer configured values.
- `filter_tasks(..., workstream=)` matches `properties["WORKSTREAM"]` exactly (not
  `Task.project`).
- CLI: string `--workstream` + runtime validate + `complete_workstream`.

## Design

- `config.DEFAULT_CONFIG["workstreams"]`
- `org_write.normalize_workstream` / `set_idea_workstream` / thread through `add_task` /
  `add_idea`
- `org.filter_tasks(workstream=)`
- `report.collect_idea_tasks` / `ideas` / `tasks` / `search_idea_tasks` / `idea_row` (omit-empty)
- `cli`: capture + list flags; `wt idea workstream --set`
- `completion.complete_workstream`; add `workstream` to `REQUIRED_SHELL_COMPLETE_NAMES`

## Alternatives considered

- Code-constant enum — rejected (1A = config).
- Warn-and-accept unknown — rejected (2A = hard fail).
- Starter non-empty defaults — rejected (3A = `[]`).

## Acceptance criteria

- [x] Config `workstreams: []` by default; configured values are the only legal writes.
- [x] `wt idea … --workstream X` and `wt add … --workstream X` write `:WORKSTREAM:` or error.
- [x] `wt idea workstream ID --set X` updates ideas; no task mutator in this spec.
- [x] `wt ideas --workstream X` and `wt tasks --workstream X` filter correctly.
- [x] `idea_row` / show JSON include omit-empty `workstream`.
- [x] Project `AI-workstreams` remains independent of the workstream facet.
- [x] Unknown write raises; shell completion lists configured streams.

## Test plan

- **Automated:** `tests/test_workstream.py` — normalize hard-fail; capture write; idea mutator;
  filter ideas+tasks; JSON field; empty config rejects all writes. **Executed 2026-07-28:**
  `uv run pytest tests/test_workstream.py tests/test_completion.py` — 37 passed.
- **Manual:** set `workstreams: [ops, platform]` in config; capture+filter round-trip.
- **Regression:** ideas/tasks/completion covered by the suite above.

## Rollout / migration

Users add `workstreams:` to config when ready. No data migration. Stale `:WORKSTREAM:` values
from hand-edits remain readable.

## Definition of done

- [x] AC met; tests pass; ledger updated; SPEC-0087 breakdown checked for this child.

## Open questions

(none — IDEA-108 dispositions locked)
