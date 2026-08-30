---
id: SPEC-0096
title: "Filter parity for wt next, hub, and agenda"
status: done
owner: user
created: 2026-07-29
updated: 2026-07-29
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-112
parent: SPEC-0087
tags: [ideas, tasks, filters, cli, hub, agenda]
---

## Context

Child of [SPEC-0087](./0087-workstreams-and-concern-separation-routing.md). IDEA-112 asked for
browse filters on ideas and “the same” elsewhere. Ideas/tasks already have full axes
(0086–0094). Residual: `wt next`, `wt hub`, `wt agenda`. Human: full parity.

## Goals / Non-goals

**Goals**
- Same idea filter axes on `wt next` and hub ideas: `--state` `--kind` `--tag` `--project`
  `--workstream` `--priority`.
- Same task-relevant axes on hub today/open slice and agenda: `--state` `--tag` `--project`
  `--workstream` `--priority` (+ `--kind` when `--ideas` includes ideas).

**Non-goals**
- Rebuilding ideas/tasks filters; filtering hub internal/outbound specs arrays; multi-value OR
  filters; `--sort` on next/hub/agenda.

## Decision

- Reuse `filter_tasks` + `idea_kind` narrowing (same as `collect_idea_tasks`).
- Hub: filters apply to `ideas` and to the `today` task lists; specs arrays unchanged.
- Agenda: filters apply to the corpus before `_agenda_buckets` (tasks always; ideas only if
  `--ideas`).

## Design

- `collect_next_tasks` / `next_ideas` / `hub_payload` / `hub_today_payload` /
  `hub_open_tasks_payload` / `agenda` take the filter kwargs.
- CLI: mirror `wt ideas` / `wt tasks` option names on next/hub/agenda.
- Tests: `tests/test_filter_parity.py`.

## Alternatives considered

- next-only v1 — rejected (human: full parity across residual commands).
- Hub specs filtering — rejected (ideas + task slice only).

## Acceptance criteria

- [x] `wt next` accepts the full ideas filter set; Rich + JSON agree.
- [x] `wt hub --json` filters ideas + today/open tasks; internal/outbound unchanged by filters.
- [x] `wt agenda` filters dated rows; `--kind` only meaningful with `--ideas`.
- [x] Omitting filters preserves prior default behavior.

## Test plan

- **Automated:** `tests/test_filter_parity.py`. **Executed 2026-07-29:**
  `uv run pytest tests/test_filter_parity.py tests/test_hub.py tests/test_agenda.py
  tests/test_workflow.py` — 34 passed.
- **Manual:** `wt next --project Meta-Tools`; `wt hub --json --kind bug`; `wt agenda --tag x`.
- **Regression:** next/hub/agenda suites above.

## Rollout / migration

Additive flags only.

## Definition of done

- [x] AC met; tests pass; ledger + SPEC-0087 breakdown updated.

## Open questions

(none)
