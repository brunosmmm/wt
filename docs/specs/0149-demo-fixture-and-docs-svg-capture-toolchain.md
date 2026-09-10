---
id: SPEC-0149
title: "Demo fixture and docs SVG capture toolchain"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0148
tags: [docs]
depends_on: [SPEC-0148]
source_idea: IDEA-383
---

## Context

Child of [SPEC-0148](./0148-example-heavy-docs-svg-captures-and-workflow.md). Without a
regenerable SVG pipeline, guides cannot show real CLI/TUI output.

## Goals / Non-goals

**Goals**

- `scripts/docs-capture.py` seeds a temp demo corpus and writes SVGs under
  `docs/product/assets/captures/`.
- CLI captures via Rich `Console(record=True).save_svg`.
- TUI captures via `IdeaDesk.export_screenshot` under `run_test`.
- Pytest asserts required capture files exist and exceed a minimum size.

**Non-goals**

- Full guide rewrite (IDEA-385).
- Diagram pages (IDEA-384).
- Live-org captures.

## Decision

One script, fixed demo titles, patch module-level `console` bindings in `wt.console` and
`wt.report`. Commit generated SVGs so docs build without running capture in CI (CI still
asserts files exist; optional regen job later).

## Design

Required outputs (initial set):

| File | Source |
|------|--------|
| `cli-ideas.svg` | `report.ideas` |
| `cli-next.svg` | `report.next_ideas` |
| `tui-desk.svg` | `IdeaDesk` after pause |

## Acceptance criteria

- [x] `uv run python scripts/docs-capture.py` writes the required SVGs.
- [x] SVGs are valid enough to embed (`<svg` present) and non-trivial size.
- [x] `tests/test_docs_captures.py` asserts required paths.
- [x] `mkdocs build --strict` still passes with at least one guide embedding a capture.

## Test plan

- **Automated:** `tests/test_docs_captures.py`; mkdocs strict.
- **Manual:** open an embedded SVG in the served site.
- **Regression:** docs test suite green.

## Definition of done

- [x] AC met; tests pass; ledger updated; IDEA-383 reconciled.

## Open questions

_(none)_
