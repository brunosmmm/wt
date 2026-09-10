---
id: SPEC-0156
title: "Architecture and lifecycle pages"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0153
tags: [docs]
depends_on: [SPEC-0153]
source_idea: IDEA-394
---

## Context

Child of SPEC-0153. Storage is fragmented across config, XDG data/outbox, org corpus, and
package `docs/specs`. “Project” is overloaded; archive/state rules (e.g. RESEARCHED,
EXPORTED) are under-taught; DoD (spec vs idea) is blurry.

## Goals / Non-goals

**Goals**

- One topology page (or concept section) covering where state lives.
- Lifecycle/state machine teaching including RESEARCHED and idea vs spec terminal states.
- Project-identity glossary + DoD matrix.
- Mermaid diagrams (Wave D) sufficient for cold architects.

**Non-goals**

- Changing runtime archive behavior.
- Team RACI swimlanes (deferred).

## Decision

Add/extend `docs/product/concepts/` pages with Mermaid; link from workflows + guides.
Truth matches code (`org` keywords, `wt spec verify`, reconcile) — cite behavior, don’t invent.

## Design

Suggested pages (exact filenames flexible):

- `concepts/architecture.md` — topology diagram.
- `concepts/lifecycle.md` (or extend existing) — states + DoD matrix.
- Glossary updates for project / outbox / portable / internal.

## Acceptance criteria

- [x] Topology page in nav under Concepts.
- [x] Lifecycle/DoD matrix documents spec `done` vs idea PROMOTED/EXPORTED/SHIPPED + verify.
- [x] RESEARCHED (or equivalent real keyword) documented accurately per code.
- [x] `mkdocs build --strict` passes.

## Test plan

- **Automated:** content needles in a docs test; mkdocs strict.
- **Manual:** render Mermaid on docs serve.
- **Regression:** workflows page still builds.

## Definition of done

- [x] AC met; test plan executed; ledger updated; IDEA-394 reconciled.

## Open questions

- None blocking accept.


## Shipped notes

Added `concepts/architecture.md` + `concepts/lifecycle.md`; glossary refreshed; nav wired; mkdocs strict + docs tests green.
