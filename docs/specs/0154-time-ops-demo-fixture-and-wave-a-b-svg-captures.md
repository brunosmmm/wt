---
id: SPEC-0154
title: "Time+ops demo fixture and Wave A/B SVG captures"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0153
tags: [docs]
depends_on: [SPEC-0153, SPEC-0149]
source_idea: IDEA-392
---

## Context

Child of [SPEC-0153](./0153-full-surface-product-docs-remediation.md). Existing
`scripts/docs-capture.py` only seeds ideas; time/agenda/tasks surfaces render empty
and are missing from `docs/product/assets/captures/`.

## Goals / Non-goals

**Goals**

- Seed deterministic `history.jsonl` (+ mappings) and org tasks in the capture fixture.
- Emit Wave A/B SVGs and commit them under `docs/product/assets/captures/`.
- Extend `tests/test_docs_captures.py` to require the new paths.

**Non-goals**

- Guide rewrites (SPEC-0155).
- Wave C spec/projects captures (SPEC-0158).
- Architecture Mermaid pages (SPEC-0156).

## Decision

Extend `scripts/docs-capture.py` only (no product CLI changes). Write fictional history
days relative to “today” in the demo timezone so `report --week` / bare dashboard are
non-empty. Seed a few SCHEDULED org tasks for agenda/tasks. Call report APIs with a
recording Rich console the same way ideas captures already work.

## Design

Required new capture files (filenames stable):

| File | Command / surface |
|------|-------------------|
| `cli-wt-dashboard.svg` | bare `wt` (today + this week rules) |
| `cli-report-week.svg` | `report(cfg, week="now")` |
| `cli-topics-unmapped.svg` | `topics(cfg, unmapped=True)` |
| `cli-map.svg` | successful `map` confirmation (or topics after map) |
| `cli-review-week.svg` | `review(cfg, week="now")` |
| `cli-agenda.svg` | `agenda(cfg, day="now")` |
| `cli-tasks.svg` | `tasks(cfg)` |

Retain existing ideas/TUI captures. Hub may stay as JSON wall for now; optional
`cli-ideas` clock glyph already covered if an open clock is seeded.

Fixture:

- `data_dir/history.jsonl` — several closed days with base topics (`acme/...`, unmapped raw).
- `mappings.yaml` — map at least one topic so map-success and unmapped contrast both work.
- Org capture/tasks file — TODO items with SCHEDULED stamps in range.

## Alternatives considered

- **Monkeypatch assemble in the script** — rejected; prefer real history.jsonl so regen
  matches production code paths.
- **Check in a static history fixture file** — optional later; generating inside the script
  keeps one entrypoint.

## Acceptance criteria

- [x] Capture script writes all Wave A/B SVG filenames above (non-trivial `<svg>`).
- [x] Fixture does not read the developer’s live XDG org/history.
- [x] `tests/test_docs_captures.py` asserts the new required SVG set.
- [x] `uv run python scripts/docs-capture.py` exits 0; pytest docs captures green.

## Test plan

- **Automated:** extend `tests/test_docs_captures.py`; run that file + capture script.
- **Manual:** open a couple new SVGs in a browser/editor; confirm non-empty tables.
- **Regression:** existing capture tests still pass.

## Rollout / migration

Regen commits the new SVGs; no runtime migration.

## Definition of done

- [x] AC met; test plan executed; ledger updated; IDEA-392 reconciled.

## Open questions

- None.


## Shipped notes

`scripts/docs-capture.py` seeds history.jsonl + Claude jsonl + org tasks; Wave A/B SVGs committed under `docs/product/assets/captures/`.
