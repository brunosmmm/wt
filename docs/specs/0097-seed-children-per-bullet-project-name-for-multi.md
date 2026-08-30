---
id: SPEC-0097
title: "seed-children per-bullet (project: Name) for multi-project epics"
status: done
owner: user
created: 2026-07-29
updated: 2026-07-29
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-121
depends_on: [SPEC-0043, SPEC-0095]
tags: [epic, seed-children, projects, routing]
---

## Context

SPEC-0043 seeds every Breakdown child with the epic’s single `target_project`. SPEC-0095
requires multi-project fan-out; EXAMPLE-0004 hit the bug. Dispositions (IDEA-121): annotate
bullets with `(project: Name)`; unknown annotated name **hard-fails** (no soft-warn);
omitted annotation falls back to epic `target_project`; headings stay unique under the epic;
new SPEC (do not rewrite done SPEC-0043); update CLI + skills + TEMPLATE-epic together.

## Goals / Non-goals

**Goals**
- Parse `(project: Name)` from Breakdown title segment; strip before idea heading.
- Fallback to epic `target_project` when annotation absent.
- Hard-fail seed if annotation names a project not in the SPEC-0095 map
  (`known_projects` ∪ `outbox_targets` ∪ Meta-Tools).
- Document in TEMPLATE-epic, wt-new-work, wt-seed / orient as needed.

**Non-goals**
- Soft-warn paths; `[@Name]` syntax; frontmatter `child_projects` map; changing
  heading-only idempotency; PROVENANCE INDEX noise.

## Decision

- Regex on raw bullet text **before** `_breakdown_idea_title` strip: optional
  `(project: <Name>)` anywhere in the line (case-insensitive match against known names;
  canonical known spelling stored on the idea).
- Title for heading/idempotency = existing `_breakdown_idea_title` on text with annotation
  removed.
- Validate Name via membership in `projects_payload` names.
- SPEC-0043 remains `done`; this spec extends behavior.

## Design

- `specs.parse_breakdown_project(item) -> (title_text, project|None)`
- `seed_ideas_from_epic` uses per-item project or epic default; raises `ValueError` on unknown
- Tests: annotation honored; omit → epic project; unknown → fail; idempotent
- TEMPLATE-epic Breakdown example; skill one-liners

## Alternatives considered

- Soft-warn + fallback — rejected (human: no warn; hard-fail instead).
- `[@Name]` — rejected (not org/markdown-native here).

## Acceptance criteria

- [x] Bullet with `(project: Example)` seeds `:PROJECT: Example` and heading without the annotation.
- [x] Bullet without annotation uses epic `target_project`.
- [x] Unknown `(project: Nope)` aborts seed with a clear error (no warn-and-continue).
- [x] Second seed-children run still idempotent on headings.
- [x] TEMPLATE-epic + wt-new-work document the annotation.

## Test plan

- **Automated:** extend `tests/test_seed_children.py` — done (`test_parse_breakdown_project`,
  `test_seed_per_bullet_project_annotation`, `test_seed_unknown_project_annotation_hard_fails`).
- **Manual:** N/A beyond automated fixture covering multi-project outbox targets.
- **Regression:** existing seed-children tests still pass (7/7 in file).

## Rollout / migration

Authxxs add annotations when fan-out is needed. Old single-project epics unchanged.

## Definition of done

- [x] AC met; tests pass; ledger updated.

## Open questions

None — locked on hard-fail for unknown annotated names.
