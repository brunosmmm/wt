---
id: SPEC-0152
title: "Org-mode storage guide and expanded CLI SVG captures"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0148
tags: [docs]
depends_on: [SPEC-0149, SPEC-0150]
source_idea: IDEA-387
---

## Context

Child of [SPEC-0148](./0148-example-heavy-docs-svg-captures-and-workflow.md). Product guides
cover commands but not **why org-mode** — file layout, enrichment outline, rotation, and
archive. CLI SVG coverage is still only `ideas` / `next` / desk.

## Goals / Non-goals

**Goals**

- Guide: `docs/product/guides/org-storage.md` (or `concepts/`) covering capture file,
  `#+TODO`, PROPERTIES, Summary / Open questions / Log, LOGBOOK clocks, rotation, archive.
- Committed example `docs/product/assets/examples/ideas-demo.org` (+ optional rotated/
  archive snippets).
- Expand `scripts/docs-capture.py` for at least: enriched `wt ideas`, `wt next`,
  `wt idea show`, `wt hub` (and keep desk).
- Embed captures + org excerpts in the guide and link from getting-started / idea→ship.

**Non-goals**

- Documenting every org property extension DSL.
- Capturing `wt report` without a transcript fixture (follow-up OK).

## Decision

Ship one workflow guide focused on org-as-storage. Demo fixture in the capture script
writes real enrichment via `wt` writers so SVG + `.org` example stay consistent. Mermaid
optional; prefer a small file-layout diagram.

## Acceptance criteria

- [x] Org storage guide exists, is in MkDocs nav, and covers rotation + enrichment.
- [x] Example `.org` fixture committed under `docs/product/assets/examples/`.
- [x] Capture script emits additional CLI SVGs including `idea show` and `hub`.
- [x] Tests assert new assets / guide keywords; `mkdocs build --strict` passes.

## Test plan

- **Automated:** extend `tests/test_docs_captures.py` + guide content test; mkdocs strict.
- **Manual:** browse the new guide on the served site.
- **Regression:** existing docs tests green.

## Definition of done

- [x] AC met; ledger updated; IDEA-387 reconciled.

## Open questions

_(none)_
