---
id: SPEC-0145
title: "Capability showcase pages for major CLI surfaces"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0141
tags: [docs]
depends_on: [SPEC-0143, SPEC-0144]
source_idea: IDEA-358
---

## Context

Child of [SPEC-0141](./0141-human-product-documentation-site-showcase.md). Guides
([SPEC-0144](./0144-product-guides-getting-started-through-outbound.md)) teach workflows;
capability pages make each major CLI surface discoverable.

Promoted from `IDEA-358`.

## Goals / Non-goals

**Goals**

- Replace stubs under `docs/product/capabilities/` with short showcase pages (what /
  when / key commands / link to guide when relevant).
- Cover every row on `capabilities/index.md`.

**Non-goals**

- Exhaustive flag encyclopedia (IDEA-359 / reference).
- Inventing commands; if unsure, omit and point to `wt <cmd> --help`.

## Decision

One Markdown page per major surface already stubbed in SPEC-0142. Keep each page to a
scope card + command table/list. Live CLI (`wt --help` / subcommand help) is the truth.

## Design

Pages: report, ideas, tui, hub, projects, sheet, clock, completion, release-archive,
tasks-agenda, meetings, skills + index. Tests: no stub markers; each file mentions its
primary command; mkdocs strict remains green.

## Alternatives considered

- **Merge into guides only** — epic requires a capability showcase distinct from
  workflow paths.

## Acceptance criteria

- [x] All capability pages listed in the index are non-stub and mention primary commands.
- [x] Index no longer says “starts as a short scope card; depth lands with IDEA-358”.
- [x] `mkdocs build --strict` passes; automated tests cover non-stub + key phrases.
- [x] No Markdown links escaping `docs/product/`.

## Test plan

- **Automated:** `tests/test_docs_product_capabilities.py`
- **Manual:** spot-check nav under Capabilities on `mkdocs serve`
- **Regression:** docs IA / guides / mkdocs tests + `uv run pytest` subset green

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] Ledger regenerated.

## Open questions

_(none)_
