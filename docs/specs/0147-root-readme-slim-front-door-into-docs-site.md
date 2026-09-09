---
id: SPEC-0147
title: "Root README slim front door into docs site"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0141
tags: [docs]
depends_on: [SPEC-0146]
source_idea: IDEA-360
---

## Context

Last child of [SPEC-0141](./0141-human-product-documentation-site-showcase.md). The
product site ([SPEC-0142](./0142-docs-product-ia-narrative-and-glossary.md)–[0146](./0146-command-reference-synced-to-live-cli.md))
now holds guides, capabilities, and reference. The root README must stop competing as a
second essay.

Promoted from `IDEA-360`.

## Goals / Non-goals

**Goals**

- README is a short front door: dual-capability pitch, install, docs site link, retention
  warning, contributor pointers.
- Relocate durable operational detail (time model, retention, meetings, XDG layout) into
  `docs/product/` so it remains findable via MkDocs.

**Non-goals**

- Deleting operational knowledge without a product-docs home.
- Changing CLI behavior.

## Decision

Rewrite `README.md` to ≤ ~120 lines. Add
`docs/product/concepts/time-and-retention.md` (sources, gap model, snapshot retention,
meetings, XDG paths, config sketch). Link it from concepts index + track-time guide.
Wire into `mkdocs.yml` nav under Concepts.

## Acceptance criteria

- [x] README line count ≤ 120 and contains dual-capability wording + install + docs link.
- [x] No full Commands encyclopedia (already removed in SPEC-0146).
- [x] Operational detail lives under `docs/product/concepts/time-and-retention.md`.
- [x] `mkdocs build --strict` passes; automated README slim test.

## Test plan

- **Automated:** `tests/test_docs_readme_front_door.py`
- **Manual:** open README + docs home; confirm no orphaned critical ops facts
- **Regression:** docs suite + reference test green

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed.
- [x] No regressions.
- [x] Spec matches shipped.
- [x] Ledger regenerated; epic child box checked; epic closable when all children done.

## Open questions

_(none)_
