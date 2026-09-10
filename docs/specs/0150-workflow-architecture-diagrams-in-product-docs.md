---
id: SPEC-0150
title: "Workflow architecture diagrams in product docs"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0148
tags: [docs]
depends_on: [SPEC-0149]
source_idea: IDEA-384
---

## Context

Child of SPEC-0148. Guides need workflow-level architecture, not only commands.

## Decision

Ship `docs/product/concepts/workflows.md` with Mermaid diagrams for dual systems,
idea→ship sequence, outbound, and desk vs CLI. D2 remains optional later (epic open Q).
Enable Mermaid fences in `mkdocs.yml`.

## Acceptance criteria

- [x] Workflows page exists and is in MkDocs nav under Concepts.
- [x] Mermaid fences render path configured in mkdocs.
- [x] Guides link to the workflows page.
- [x] `mkdocs build --strict` passes.

## Test plan

- **Automated:** mkdocs strict (existing docs tests).
- **Manual:** open Workflow architecture in the served site.
- **Regression:** docs suite green.

## Definition of done

- [x] AC met; ledger updated.
