---
id: SPEC-0151
title: "Example-heavy guides embedding SVG captures"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0148
tags: [docs]
depends_on: [SPEC-0149, SPEC-0150]
source_idea: IDEA-385
---

## Context

Child of SPEC-0148. Product guides should show real CLI/TUI output and point at workflow
architecture.

## Decision

Embed committed SVGs from `docs/product/assets/captures/` into getting-started,
idea-to-ship, and the TUI capability page; link to `concepts/workflows.md`.

## Acceptance criteria

- [x] Getting started embeds `cli-ideas.svg` and `cli-next.svg`.
- [x] Idea→ship embeds the same and links workflows.
- [x] TUI capability embeds `tui-desk.svg`.
- [x] MkDocs strict build passes.

## Test plan

- **Automated:** `tests/test_docs_captures.py` + mkdocs strict.
- **Manual:** browse embedded images on served site.
- **Regression:** docs tests green.

## Definition of done

- [x] AC met; ledger updated.
