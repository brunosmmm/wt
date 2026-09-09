---
id: SPEC-0146
title: "Command reference synced to live CLI"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0141
tags: [docs]
depends_on: [SPEC-0145]
source_idea: IDEA-359
---

## Context

Child of [SPEC-0141](./0141-human-product-documentation-site-showcase.md). Capability
pages ([SPEC-0145](./0145-capability-showcase-pages-for-major-cli-surfaces.md)) showcase
surfaces; this spec keeps a **curated command index** honest against live `--help` and
removes the root README command encyclopedia as the competing source of truth.

Promoted from `IDEA-359`.

## Goals / Non-goals

**Goals**

- Fill `docs/product/reference/index.md` with every top-level `wt` command.
- Automated test: parse `wt --help` Commands and assert each name appears in the
  reference page.
- Replace the large README “Commands” table with a short pointer to the product docs
  reference (full README slim is IDEA-360).

**Non-goals**

- Generating full flag docs per command.
- Auto-publishing help text into MkDocs on every build (curated + tested is enough).

## Decision

Curated Markdown table + pytest sync guard. README loses the stale encyclopedia table
now; IDEA-360 further shortens pitch/install.

## Acceptance criteria

- [x] Reference index lists every top-level command from `wt --help`.
- [x] Test fails if a new top-level command is added without updating the reference.
- [x] Root README no longer contains the full Commands encyclopedia table.
- [x] `mkdocs build --strict` still passes.

## Test plan

- **Automated:** `tests/test_docs_product_reference.py`
- **Manual:** compare table to `wt --help` once
- **Regression:** docs + mkdocs tests green

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed.
- [x] No regressions.
- [x] Spec matches shipped.
- [x] Ledger regenerated.

## Open questions

_(none)_
