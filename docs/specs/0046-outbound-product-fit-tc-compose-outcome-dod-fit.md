---
id: SPEC-0046
title: "Outbound product-fit: TC compose, outcome DoD, fit log"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: epic
tags: [outbound, export, REMOVED, workflow-audit]
source_idea: IDEA-057
depends_on: [SPEC-0015, SPEC-0016, SPEC-0033, SPEC-0041, SPEC-0043]
---

## Context

Promoted from `IDEA-057`. Outbound work can clear wt’s process DoD and still miss product
intent in the target (especially REMOVED). Three linked gaps from the workflow audit:

1. Epic decomposition: `parent:` children vs Breakdown→`task_base.Z` do not compose at export.
2. “Done” means mechanical AC/tests, not outcome fit.
3. No durable post-ship fit/miss signal before painful supersede.

## Goals / Non-goals

**Goals**
- One coherent outbound product-fit loop across compose → outcome bar → fit log.
- Keep internal Meta-Tools process DoD (AGENTS.md) unchanged for ordinary CLI polish.

**Non-goals**
- New `export-ready` status enum (v1).
- Mandatory demo/sign-off on every Meta-Tools typo fix.
- Rewriting REMOVED’s entire schema outside wt’s export seam.

## Decision

Ship three child specs under this epic:

1. **Compose** REMOVED epic export from `parent:` children when present.
2. **Outcome DoD** for outbound via guidance + ≥1 outcome AC or `outcome:` frontmatter.
3. **Fit log** into the source idea (thin CLI helper), documented on export/implement skills.

## Architecture / cross-cutting design

- **Outbound identity** stays PROJ-NNNN (SPEC-0041); generate remains forbidden.
- **SCHEMA** hierarchy SoT remains `parent:`; Breakdown is seed/coverage for epics.
- **REMOVED** join key remains `outbox_targets[].task_base` unless a child adds optional
  `deliverable_id`.
- **Learning loop:** implement/use → fit-log on idea → explore/supersede as needed.
- Children must not require target-repo `AGENTS.md` splices (see SPEC-0045 skill model).

## Breakdown / sub-specs

- [x] [SPEC-0047](./0047-compose-outbound-epic-children-into-REMOVED.md) — Compose
      `parent:` children into REMOVED deliverables (`done`)
- [x] [SPEC-0048](./0048-product-fit-definition-of-done-process-close-vs.md) — Outbound
      outcome DoD (`done`)
- [x] [SPEC-0049](./0049-post-export-post-ship-fit-log-before-supersede.md) — Post-ship fit
      log (`done`)

Sequencing for **implementation**: **0047** → **0048** → **0049** (0048∥0049 ok after 0047
design is stable). Leave epic open until children are `done`.

## Acceptance criteria

- [x] All three children `accepted` then `done` (authxxing) with `parent: SPEC-0046`.
- [x] Children `done`; epic closed.
- [x] Architecture above is respected by child Designs.

## Test plan

Integration-level (children own unit detail):

- **Integration:** epic with `parent:` children exports one composed TC deliverable; outbound
  export path documents outcome AC; fit-log appears on source idea Log.
- **Manual:** walk session-triage-shaped fixture (or synthetic outbox epic+children).
- **Regression:** Breakdown-only epic export and feature REMOVED export still work;
  internal AGENTS DoD unchanged.

## Rollout / sequencing

1. Accept this epic + children.
2. Implement 0047 → 0048 → 0049 (or 0048∥0049 after 0047).
3. Mark children done; keep epic open until all three done.

## Definition of done

- [x] All Breakdown children `done` or `superseded`.
- [x] Integration checks above executed.
- [x] Epic body matches what shipped.

## Open questions

_None — locked in explore of IDEA-033/034/040._
