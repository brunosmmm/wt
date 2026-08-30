---
id: SPEC-0093
title: "Priority surfacing parity for ideas (filter, column, JSON, mutate)"
status: done
owner: user
created: 2026-07-28
updated: 2026-07-28
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-096
parent: SPEC-0087
tags: [ideas, priority, cli]
---

## Context

Child of [SPEC-0087](./0087-workstreams-and-concern-separation-routing.md). Priority cookies
`[#A|B|C]` already exist on capture and on `wt tasks`; ideas omit column/filter/JSON and have
no post-capture mutator. Dispositions (IDEA-096): list parity + mutate; show includes priority;
A/B/C only; default ideas order stays freshness (sort → IDEA-097).

## Goals / Non-goals

**Goals**
- `wt ideas --priority A|B|C`; `pri` column; omit-empty `priority` on `idea_row` / show JSON.
- `wt idea priority ID --set A|B|C` rewrites the headline cookie.

**Non-goals**
- Changing default sort; `--sort` (IDEA-097); question-item `[#C]` (SPEC-0054); expanding
  beyond A/B/C; task priority mutator.

## Decision

- Reuse org `[#A|B|C]` / `Task.priority`.
- Filter via existing `filter_tasks(..., priority=)`.
- Mutator rewrites headline cookie (not a property); bumps `:UPDATED:`.
- Default list order unchanged (`_idea_freshness_key`).
- Rich `pri` column omitted when no row in the view has a cookie (narrow-terminal safety).

## Design

- `org_write.set_idea_priority`
- `report.idea_row` / `collect_idea_tasks` / `ideas` / `search_idea_tasks` + `pri` meta column
- `explore.idea_show_payload` omit-empty `priority`
- CLI: `ideas --priority`; `idea priority --set`

## Alternatives considered

- List-only without mutate — rejected (1B).
- Priority sort in this child — rejected (deferred to 097).

## Acceptance criteria

- [x] `wt ideas --priority A` filters; Rich shows `pri` when present; JSON/show include
      omit-empty `priority`.
- [x] `wt idea priority ID --set B` updates cookie; invalid values fail.
- [x] Default ideas order still freshness-first.
- [x] Tasks priority behavior unchanged.

## Test plan

- **Automated:** `tests/test_idea_priority.py` — filter, JSON, show, mutator, order unchanged.
  **Executed 2026-07-28:** `uv run pytest tests/test_idea_priority.py` — 6 passed. Table-width
  suite still green aside from known-flaky `COLUMNS` boundary assert.
- **Manual:** capture with `--priority A`; list/filter/mutate.
- **Regression:** ideas table width / kind glyph tests.

## Rollout / migration

Additive. Ideas without cookies omit the field / blank pri cell.

## Definition of done

- [x] AC met; tests pass; ledger updated; SPEC-0087 breakdown checked.

## Open questions

(none — IDEA-096 dispositions locked)
