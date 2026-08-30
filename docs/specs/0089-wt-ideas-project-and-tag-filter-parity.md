---
id: SPEC-0089
title: "wt ideas --project and --tag filter parity"
status: done
owner: user
created: 2026-07-28
updated: 2026-07-28
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-110
parent: SPEC-0087
tags: [ideas, cli, filters]
---

## Context

Child of [SPEC-0087](./0087-workstreams-and-concern-separation-routing.md). `wt tasks` filters
by `--tag` / `--project`; `wt ideas` does not, though capture already writes those fields and
`filter_tasks` already supports them. Dispositions (IDEA-110): match `Task.project` (incl.
outline/file-stem fallback); **warn** on unknown project; `--query` composes with tag/project.
`--priority` stays with IDEA-096.

## Goals / Non-goals

**Goals**
- `wt ideas --tag` and `--project` (and compose with `--state` / `--kind` / `--all` / `--query`).

**Non-goals**
- `--priority` on ideas (IDEA-096).
- New JSON schema fields (tags/project already on rows).
- Tag shell completion (tasks have none).

## Decision

Thread `tag` / `project` through `collect_idea_tasks` → `filter_tasks`, `ideas()`,
`search_idea_tasks`, and `ideas_cmd`. On `--project`, if the value is not in
`known_projects(cfg)`, print the same style of stderr warning as capture
(`_warn_unknown_associations`) but still filter (exact match → possibly empty). `--query`
applies after the filtered corpus (AND).

## Design

- `collect_idea_tasks(..., tag=None, project=None)` → `filter_tasks(..., tag=, project=)`.
- `search_idea_tasks` / `collect_idea_rows` / `ideas()` accept and forward the same kwargs.
- CLI: `--tag`, `--project` with `shell_complete=complete_project`.
- Warn helper: reuse `rules.known_projects` + stderr message mirroring org_write.

## Alternatives considered

- **Only `:PROJECT:` property** — rejected; parity with tasks uses `Task.project` (1A).
- **Silent unknown project** — rejected; warn (2B).

## Acceptance criteria

- [x] `wt ideas --tag X` / `--project P` narrow the list like `wt tasks`.
- [x] Unknown `--project` warns on stderr and returns the (possibly empty) exact-match set.
- [x] `--query` AND-composes with `--tag` / `--project`.
- [x] `--priority` not added on ideas in this spec.
- [x] JSON schema unchanged; filtered `--json` lists are subsets.

## Test plan

- **Automated:** `tests/test_ideas.py` or new cases — tag filter, project filter, warn on
  unknown project, query×project compose.
- **Manual:** `uv run wt ideas --project Meta-Tools`; unknown project shows `! unknown project`.
- **Manual/CI:** Performed 2026-07-28 — targeted pytest green.
- **Regression:** existing ideas/json/search tests green.

## Rollout / migration

None.

## Definition of done

- [x] AC met; tests pass; ledger updated; spec reflects shipped code.

## Open questions

(none — IDEA-110 dispositions locked)
