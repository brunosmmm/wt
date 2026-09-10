---
id: SPEC-0158
title: "Outbound/multi-project depth and Wave C captures"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0153
tags: [docs]
depends_on: [SPEC-0153, SPEC-0154]
source_idea: IDEA-396
---

## Context

Child of SPEC-0153. Outbound exists in guides but close-the-loop (`pull-status` / sweep /
idea `SHIPPED`) reads optional; `seed-children` and export schemes under-taught; no Wave C
SVGs.

## Goals / Non-goals

**Goals**

- Deepen outbound / multi-project product docs so reconcile is **required** ops narrative.
- Document `seed-children`, export schemes, stuck-EXPORTED recovery at a usable level.
- Add Wave C captures: projects list + at least one of `spec export` / `verify` /
  `pull-status` (fixture-safe).

**Non-goals**

- Changing export runtime behavior.
- Sheet-sync deep productization.

## Decision

Extend capture fixture with a minimal fake outbox portable (or mock print path) only as
needed for SVG; prefer capturing `wt projects` and a dry safe verify/export path. Rewrite
outbound guide sections to mandate pull-status → SHIPPED.

## Design

- New SVGs e.g. `cli-projects.svg`, `cli-spec-verify.svg` (exact set recorded when shipped).
- Guide updates under existing outbound / multi-project pages + link from weekly ops.

## Acceptance criteria

- [x] Wave C SVGs committed and required by docs capture tests.
- [x] Outbound guide states pull-status/sweep + idea SHIPPED as required close-the-loop.
- [x] `seed-children` and schemes called out with examples.
- [x] `mkdocs build --strict` passes.

## Test plan

- **Automated:** new SVG path asserts; content needles for pull-status/SHIPPED.
- **Manual:** open outbound guide + SVGs.
- **Regression:** prior outbound tests/docs green.

## Definition of done

- [x] AC met; test plan executed; ledger updated; IDEA-396 reconciled.

## Open questions

- Exact Wave C command set may trim if a surface cannot be fixture-isolated — document in
  spec body when shipping.


## Shipped notes

Outbound/multi-project guides mandate pull-status/sweep→SHIPPED; document seed-children + schemes; Wave C SVGs `cli-projects.svg` + `cli-spec-schemes.svg` via docs-capture.
