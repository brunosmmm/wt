---
id: SPEC-0092
title: "Hub tasks / today slice"
status: done
owner: user
created: 2026-07-28
updated: 2026-07-28
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-111
parent: SPEC-0087
tags: [hub, tasks, json, cli]
---

## Context

Child of [SPEC-0087](./0087-workstreams-and-concern-separation-routing.md). Hub is ideas+specs
only; agents need a day-execution slice without dumping ~100+ undated CATEGORIZE inbox items.
Dispositions (IDEA-111): default agenda today+overdue; CLI options for other slices; co-ship
`wt tasks --json`; nested hub key `{date, overdue, tasks}`; exclude/cap noisy states.

## Goals / Non-goals

**Goals**
- Shared `task_row` + `wt tasks --json` (`wt.tasks.v1`).
- Additive hub key `today: {date, overdue, tasks}` (non-idea, agenda-shaped for “today”).
- `wt hub --json --tasks-slice today|open|none` (default `today`).

**Non-goals**
- Separate day command; Rich hub table; changing `wt.hub.v1` schema string.
- Dumping all open tasks into the default hub payload.

## Decision

- **`task_row(cfg, task)`:** stable agent row — `id`, `state`, `heading`, `tags`, omit-empty
  `priority`/`project`/`scheduled`/`deadline`/`topic_key`/`workstream`/`epic`.
- **`wt tasks --json`:** same filters as Rich list; envelope
  `{"schema":"wt.tasks.v1","tasks":[…]}`.
- **Hub default:** `today.date` = local today ISO; `today.tasks` = unique non-idea tasks with
  SCHEDULED or DEADLINE on that day; `today.overdue` = non-idea not-done with DEADLINE before
  today. Both lists drop noise states (default `CATEGORIZE`).
- **`--tasks-slice open`:** replace nested today with
  `{"slice":"open","tasks":[…]}` — open actionable non-ideas, noise excluded, capped
  (`hub_tasks_cap`, default 40).
- **`--tasks-slice none`:** omit the tasks block entirely.
- Config: `hub_noise_states: ["CATEGORIZE"]`, `hub_tasks_cap: 40`.

## Design

- `report.task_row` / `hub_today_payload` / `hub_open_tasks_payload` /
  `hub_payload(..., tasks_slice=)` / `tasks(..., as_json=)`
- CLI: `tasks --json`; `hub --tasks-slice`
- Tests: `tests/test_hub.py` + `tests/test_tasks.py` JSON paths

## Alternatives considered

- All-open dump in hub — rejected (noise).
- Flat `tasks` array only — rejected (3C nested).
- Defer `wt tasks --json` — rejected (2A co-ship).

## Acceptance criteria

- [x] `wt tasks --json` emits `wt.tasks.v1` with `task_row` fields; filters compose.
- [x] Default `wt hub --json` includes `today: {date, overdue, tasks}` (ideas excluded).
- [x] Noise state `CATEGORIZE` excluded from hub task lists; open slice capped.
- [x] `--tasks-slice open|none` works; schema string remains `wt.hub.v1`.
- [x] Pre-existing hub fields unchanged (ideas/internal/outbound/stale/…).

## Test plan

- **Automated:** hub envelope + today membership + overdue + noise exclusion; tasks --json
  filter; slice open/none. **Executed 2026-07-28:**
  `uv run pytest tests/test_hub.py tests/test_tasks.py` — 12 passed.
- **Manual:** `wt hub --json | jq .today` against live org.
- **Regression:** existing hub + tasks tests.

## Rollout / migration

Additive JSON only. Agents that ignore unknown keys keep working.

## Definition of done

- [x] AC met; tests pass; ledger updated; SPEC-0087 breakdown checked.

## Open questions

(none — IDEA-111 dispositions locked)
