---
id: SPEC-0043
title: "Epic promote seeds child ideas; known_epics includes outbound"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
tags: [skills, epic, ideas, outbound, ergonomics]
source_idea: IDEA-052
depends_on: [SPEC-0003, SPEC-0015, SPEC-0018, SPEC-0020, SPEC-0033]
---

## Context

Promoted from `IDEA-052`. Promoting to outbound epic `DEMO-0001` left Breakdown
slices as checkboxes only. `--epic DEMO-0001` warned because `known_epics` only
scanned internal specs. Outbound `--epic` scaffolding used feature `TEMPLATE.md`.

## Goals / Non-goals

**Goals**
- `known_epics` lists internal and outbound `kind: epic` ids.
- Outbound `wt spec new --epic` uses `TEMPLATE-epic.md`.
- `wt spec seed-children <EPIC-ID>` mints INCUBATE ideas from Breakdown (idempotent).
- `/wt-new-work` runs seed-children after epic accept.

**Non-goals**
- Auto-promoting children to specs; outbound generate (SPEC-0041).

## Decision

Fix epic registry + outbound epic scaffold; add `seed-children` CLI invoked by the skill after
epic accept.

## Design

### `known_epics`
Internal `docs/specs/[0-9]*.md` plus outbox `*/*.md` with `kind: epic`.

### Outbound `--epic`
`scaffold_outbound(..., epic=True)` reads `TEMPLATE-epic.md`; `promote_idea` forwards the flag.

### `seed_ideas_from_epic` / `wt spec seed-children`
Resolve epic path; require `kind: epic`; `spec_tasks` Breakdown bullets → short titles;
`add_idea` with `:EPIC:` + outbound `target_project`; skip existing epic+heading pairs.

### Skills
`wt-new-work` step: after accepting an epic, `wt spec seed-children <id>`.

## Alternatives considered

- Skill-only seeding — rejected (need testable CLI).
- Seed at empty scaffold time — rejected (Breakdown filled at accept).

## Acceptance criteria

- [x] `known_epics` includes outbound epic ids.
- [x] `--epic` on capture accepts outbound ids without unknown-epic warn when present.
- [x] Outbound `--epic` scaffold is `kind: epic` from `TEMPLATE-epic.md`.
- [x] `seed-children` creates ideas; second run is a no-op for same headings.
- [x] `wt-new-work` documents the step.
- [x] Tests in `tests/test_seed_children.py`.

## Test plan

- **Automated:** `tests/test_seed_children.py`; full pytest green.
- **Manual:** `wt spec seed-children DEMO-0001` → no new ideas (048–051 already
  seeded); `DEMO-0001 in known_epics`.
- **Regression:** internal epic promote unchanged.

## Rollout / migration

None required. Existing epics: run `wt spec seed-children` once if needed.

## Definition of done

- [x] AC met; tests green; ledger current.

## Open questions

_None._
