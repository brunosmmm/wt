---
id: SPEC-0094
title: "Optional --sort on wt ideas and wt tasks (not global)"
status: done
owner: user
created: 2026-07-28
updated: 2026-07-28
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-097
parent: SPEC-0087
tags: [ideas, tasks, sort, cli]
---

## Context

Child of [SPEC-0087](./0087-workstreams-and-concern-separation-routing.md), after
[SPEC-0093](./0093-priority-surfacing-parity-for-ideas-filter-column.md). Sorting already exists
per-command; there is no override. Dispositions (IDEA-097): leave `wt next` alone; keys
`freshness`+`priority` only; Rich + `--json`; `--query` stays relevance-first.

## Goals / Non-goals

**Goals**
- Optional `--sort freshness|priority` on `wt ideas` and `wt tasks` (Rich + JSON).
- Optional `--desc` to reverse.
- Defaults unchanged when `--sort` omitted.

**Non-goals**
- Agenda/digest/hub/next `--sort`; global sort DSL; overriding `--query` ranking.

## Decision

- Ideas default: `_idea_freshness_key`. Tasks default: `_task_sort_key`.
- `--sort priority`: A < B < C < missing (`Z`), then stable secondary (ideas: freshness;
  tasks: project/heading).
- `--sort freshness`: ideas = UPDATED stamp; tasks = SCHEDULED then DEADLINE date (missing last).
- `--query` ignores `--sort` (relevance-first).
- Hub / `wt next` unchanged.

## Design

- `report._apply_sort` / `_idea_priority_key` / `_task_freshness_key` / `_task_priority_key`
- `collect_idea_tasks(..., sort=, desc=)` / `ideas` / `tasks`
- CLI: `--sort` + `--desc` on both list commands
- Tests: `tests/test_sort.py`

## Alternatives considered

- Include `wt next` — rejected.
- Extra keys (project/state) — rejected for v1.
- Sort overrides `--query` — rejected.

## Acceptance criteria

- [x] Omitting `--sort` preserves current ideas/tasks order.
- [x] `--sort priority` / `--sort freshness` (+ `--desc`) reorder Rich and JSON.
- [x] `wt ideas --query … --sort priority` stays score-ordered.
- [x] `wt next` / hub / agenda order unchanged.

## Test plan

- **Automated:** `tests/test_sort.py` — defaults; priority/freshness; desc; query ignores.
  **Executed 2026-07-28:** `uv run pytest tests/test_sort.py tests/test_tasks.py
  tests/test_idea_priority.py` — 18 passed.
- **Manual:** `wt ideas --sort priority`; `wt tasks --sort freshness --json`.
- **Regression:** ideas/tasks suites above.

## Rollout / migration

Additive CLI flags only.

## Definition of done

- [x] AC met; tests pass; ledger + epic breakdown updated.

## Open questions

(none — IDEA-097 dispositions locked)
