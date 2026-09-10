---
id: SPEC-0163
title: "Home page thesis: mini-spec workflow first, passive time secondary"
status: done
owner: user
created: 2026-09-10
updated: 2026-09-10
milestone: "M8: product documentation"
kind: feature
tags: [docs]
depends_on: [SPEC-0142, SPEC-0155, SPEC-0162]
---

## Context

The product docs home listed passive time first and under-drove the mini-spec / verify
loop. A first rewrite swung too hard (“not an idea catalog”, “Passive time (secondary)”).
Corrected copy keeps **both** truths: ideas triage/catalog **and** governing spec →
verify, with hours present without rank labels.

## Goals / Non-goals

**Goals**

- Home leads with ideas + lifecycle (including verify), then passive time — no “secondary”
  labels, no “not a catalog” negation.
- Short Start here; guides for depth.
- Getting started path order: workflow, then agents, then hours.
- Docs IA tests lock the softer constraints.

**Non-goals**

- Rewriting all guides; CLI changes.

## Decision

Calm dual-surface home: (1) ideas & lifecycle with mini-spec + verify named, (2) passive
time. Both SVGs retained. No extremity labels.

## Design

- `docs/product/index.md` — dual list, pipeline one-liner, Start here, Also.
- `guides/getting-started.md` — Path A ideas/ship, B agents, C hours.
- `mkdocs.yml` site_description; `tests/test_docs_product_ia.py` order + no negation.

## Acceptance criteria

- [x] Ideas/lifecycle before passive time; verify (or Test plan) named.
- [x] No “not an idea catalog”; no “(secondary)” on time.
- [x] Catalog/triage still implied (ideas, hub, next).
- [x] Clock supplemental wording kept; docs tests + mkdocs build OK.

## Test plan

- `uv run pytest tests/test_docs_product_ia.py tests/test_docs_captures.py -q`
- `uv run mkdocs build --strict`

## Clock Log

CLOCK-IN: 2026-09-10T07:51:00-04:00
CLOCK-OUT: 2026-09-10T07:56:00-04:00

## Definition of done

- [x] AC met; tests green; ledger current; status `done`.

## Open questions

None.
