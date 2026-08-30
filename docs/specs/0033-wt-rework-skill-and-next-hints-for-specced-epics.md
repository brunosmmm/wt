---
id: SPEC-0033
title: wt-rework skill and next-hints for SPECCED epics
status: done
owner: user
created: 2026-07-23
updated: 2026-07-23
milestone: "M4: cli ergonomics"
kind: feature
tags: [skills, workflow, ideas, epics, ergonomics]
source_idea: IDEA-021
depends_on: [SPEC-0017, SPEC-0023, SPEC-0003, SPEC-0024]
---

## Context

Promoted from idea `IDEA-021`.

The idea→spec pipeline is one-way after promote. Once `:SPEC:` is set,
`workflow.next_step_for_idea` often returns `wt tasks` (especially `PROMOTED`, and
outbound specs once exported) even when the linked work is an **incomplete epic**.
There is no agent skill for “design was wrong” (**rework**) or “epic not finished —
add children” (**extend**).

Mechanisms already exist: supersede (AGENTS.md), `parent:` children (SPEC-0003),
`wt spec new --force`, Breakdown-driven `wt spec generate` (idempotent). Missing:
playbook + next-hints.

Motivating case: `IDEA-001` → outbound `DEMO-0001` (`kind: epic`, `accepted`,
exported, unchecked Breakdown, **zero** child specs) still hints `wt tasks`.

## Goals / Non-goals

**Goals**
- Ship installable skill `skills/wt-rework/` with an explicit **rework | extend** fork.
- Update `next_step_for_idea` so a linked **epic** that is not complete (open Breakdown
  checkboxes and/or zero/incomplete children) hints `/wt-rework {idea_id}` instead of
  premature `wt tasks`.
- Document the loop in `docs/WORKFLOW.md` and `skills/wt-orient`.
- Register the skill in the skills list / SPEC-0017 install set (same pattern as
  `wt-explore`).
- Same skill for internal and outbound; outbound verify steps include `wt spec export`
  after new children are accepted.

**Non-goals**
- New idea TODO states or a second skill file (`wt-extend-epic`).
- Auto-detecting “user dissatisfied” (rework is human-opt-in via the skill).
- Changing supersede semantics or silently rewriting past-`draft` specs.
- Building a full epic dashboard CLI.

## Decision

One skill `/wt-rework`: gate on idea with `:SPEC:`; ask rework vs extend; drive existing
CLI/spec conventions. Teach `next_step_for_idea` to treat “exported outbound epic with
open Breakdown / no children” as **extend**, not done. Hint string: `/wt-rework {idea_id}`.

## Design

### Skill `skills/wt-rework/SKILL.md`

Thin playbook (like `wt-explore` / `wt-new-work`):

0. Gate: `wt idea show <ID>` — must have `:SPEC:` / linked spec id.
1. Fork (require explicit user choice if unclear):
   - **Rework** — Log why on the idea (`wt idea log`); authxx a **new** spec that
     `supersedes` the bad one (or rare `wt spec new --force` restart with rationale);
     set old `status: superseded` + `superseded_by`; never silent rewrite.
   - **Extend** — for `kind: epic`: list Breakdown gaps / missing children; scaffold
     child specs with `parent: <epic-id>` (internal or outbound per routing); update
     epic Breakdown checkboxes as children land; `accepted` → `wt spec generate`
     (idempotent); outbound → `wt spec export` when ready.
2. Verify: lint/ledger for internal; show next hint; do not mark epic `done` until
   children are done/superseded (existing lint).

### `next_step_for_idea` (`src/wt/workflow.py`)

After loading linked spec (path + frontmatter + body), if `kind == epic` and status in
`accepted|in-progress|done` — **before** the `PROMOTED → wt tasks` short-circuit and
before outbound export/tasks:

1. Resolve children (`parent == epic.id`) in the same namespace (internal `docs/specs/` or
   outbox project dir).
2. Parse epic body Breakdown for unchecked `- [ ]` items (best-effort).
3. If any child not in `{done, superseded}` **or** Breakdown has unchecked items **or**
   (epic has Breakdown checkbox items and zero children): return `/wt-rework {idea_id}`.
4. Else keep current behavior (`wt tasks` / export / generate).

Rework remains opt-in (no automatic “dissatisfied” signal).

### Docs

- `docs/WORKFLOW.md`: SPECCED/PROMOTED row mentions `/wt-rework` for redesign or extend.
- `skills/wt-orient`: list `wt-rework` in the skill chain after generate/export.

### Tests

- Unit: incomplete epic (unchecked Breakdown / no children) → `/wt-rework`;
  complete epic → `wt tasks`.
- Skills install list includes `wt-rework`.

## Alternatives considered

- **Two skills** — rejected; shared gate and docs; fork inside one skill is enough.
- **New idea state REWORK** — rejected; Log + supersede suffice.
- **Only docs, no next_step change** — rejected; IDEA-001 shows hints actively mislead.

## Acceptance criteria

- [x] `skills/wt-rework/SKILL.md` exists, installable, documents rework vs extend forks.
- [x] `wt skills list` / install set includes `wt-rework`.
- [x] `next_step_for_idea` for an incomplete linked epic hints extend/`/wt-rework`, not bare
      `wt tasks` (covers outbound accepted+exported with open Breakdown).
- [x] Complete epics (all children done/superseded, no open Breakdown) still hint `wt tasks`
      (or export when applicable).
- [x] WORKFLOW + wt-orient mention the skill.
- [x] Tests + full pytest green.

## Test plan

- **Automated:** `tests/test_workflow.py` epic-incomplete vs complete; `tests/test_skills.py`
  lists `wt-rework`.
- **Manual:** `wt next --all` shows `/wt-rework IDEA-001` for the AI-workstreams epic
  (was `wt tasks`); `uv run wt skills install` links `wt-rework`.
- **Regression:** existing next-step cases; `uv run pytest` (281 passed).

## Rollout / migration

Ship skill + hint logic. No org data migration. Re-`wt skills install` for agents.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; pytest green; manual check noted.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

_None — decisions locked in explore._
