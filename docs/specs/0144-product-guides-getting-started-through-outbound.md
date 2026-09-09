---
id: SPEC-0144
title: "Product guides: getting started through outbound"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0141
tags: [docs]
depends_on: [SPEC-0143]
source_idea: IDEA-357
---

## Context

Child of [SPEC-0141](./0141-human-product-documentation-site-showcase.md). After
[SPEC-0142](./0142-docs-product-ia-narrative-and-glossary.md) stubs and
[SPEC-0143](./0143-mkdocs-material-docs-site-toolchain.md) themed builds, guides must
carry real workflow prose so newcomers do not need SPECs or the root README essay.

Promoted from `IDEA-357`.

## Goals / Non-goals

**Goals**

- Fill `docs/product/guides/{getting-started,track-time,idea-to-ship,outbound,multi-project}.md`
  plus a short `guides/index.md` overview.
- Day-1 install, weekly time loop, idea→ship (internal + outbound), multi-project fan-out.
- Commands match live CLI; no invented flags.

**Non-goals**

- Capability deep-dives (IDEA-358).
- Full command reference sync (IDEA-359).
- Root README slim-down (IDEA-360).
- Copying SPECs into guides.

## Decision

Rewrite guide stubs from `docs/WORKFLOW.md` + README quick-start/time sections into
MkDocs-safe Markdown (no links escaping `docs_dir`). Keep guides imperative and short;
point to Concepts/Capabilities for vocabulary and surface detail.

## Design

| Page | Job |
|------|-----|
| `getting-started.md` | Install (`uv`), verify real `wt`, completion, first dashboard + first idea |
| `track-time.md` | Topics → map → report → snapshot; passive vs clock-in |
| `idea-to-ship.md` | Capture → explore → accepted spec → generate/verify (internal) |
| `outbound.md` | projects add → export → implement portable → pull-status/SHIPPED |
| `multi-project.md` | `wt projects --json`, epic fan-out, research roots |
| `index.md` | Table of guides (already); drop stub language |

Automated: assert each guide file has no `**Status:** stub` and contains key command
strings; `mkdocs build --strict` still passes.

## Alternatives considered

- **Leave WORKFLOW.md as the only guide** — epic requires themed guides; WORKFLOW stays a
  cheatsheet pointer until absorbed.
- **One mega-guide** — lost to match IA nav and skimmability.

## Acceptance criteria

- [x] Five guide pages (+ index) are non-stub and cover install, time loop, idea→ship
      internal, outbound, multi-project.
- [x] No Markdown links that escape `docs/product/` (strict build green).
- [x] Automated tests assert non-stub + key phrases; mkdocs strict still passes.
- [x] Guides do not invent CLI flags (spot-check against `wt --help` / WORKFLOW).

## Test plan

- **Automated:** extend `tests/test_docs_product_ia.py` or add
  `tests/test_docs_product_guides.py` — no stub markers; required substrings per file;
  reuse mkdocs strict test.
- **Manual:** cold read getting-started + idea-to-ship on `mkdocs serve`.
- **Regression:** `uv run pytest` green; SPEC-0142/0143 tests still pass.

## Clock Log

Prefer `wt idea clock-in` / `clock-out` on IDEA-357.

## Rollout / migration

Land Markdown under `docs/product/guides/`; site rebuilds automatically.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_(none)_
