---
id: SPEC-0162
title: "Document default wt-native portable as lightweight verify workflow"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
tags: [docs, export, outbound]
depends_on: [SPEC-0015, SPEC-0016, SPEC-0141, SPEC-0158]
---

## Context

Product docs named `wt-native` as the default export scheme in a one-line schemes table, but
did not explain that this **is** wt’s default outbound workflow: a lightweight governing
markdown portable (Context / Decision / Design / Acceptance criteria / Test plan) plus a
consumption contract that pushes implement → verify before `done`. Operators and agents
under-learned why `/wt-verify` and AC+Test plan exist on the portable. The schemes table also
still showed a duplicate/wrong third row after branded-adapter removal (SPEC-0161). Scrub
residue left `authxx` typos in product docs (`author` / `authoritative`).

## Goals / Non-goals

**Goals**

- Expose the default portable story in product docs: `wt-native` = lightweight
  verification-enforcing workflow (not an optional fancy export).
- Contrast briefly with `plain-md`.
- Fix schemes table + `authxx` typos in `docs/product/` and the in-repo `docs/WORKFLOW.md`
  cheatsheet.
- Wire the story from home / outbound / lifecycle / concepts glossary / mkdocs nav.

**Non-goals**

- Changing export runtime, scheme registration, or required fields.
- Reintroducing any branded third scheme.
- Rewriting the full agent skills corpus.

## Decision

Add a short **Concepts** page for the default portable / export schemes, deepen the
Outbound “Schemes” section with the verify-enforcing narrative, and link it from the docs
front door and lifecycle. Keep `wt-native` vs `plain-md` accurate to `wt spec schemes`.

## Design

- New: `docs/product/concepts/portable-default.md` — what lands in the target repo, required
  sections, contract role, `/wt-implement-spec` → `/wt-verify`, pull-status → SHIPPED.
- Updated: `guides/outbound.md` schemes section; `concepts/index.md` glossary; lifecycle;
  home; workflows outbound note; guides index; `docs/WORKFLOW.md` outbound snippet; mkdocs
  nav.
- Fixed `authxx` → `author` / `authoritative` in product docs + `docs/WORKFLOW.md`.

## Alternatives considered

- **Only expand outbound.md** — under-discovers the concept from Concepts/home.
- **New guide page** — overkill; this is vocabulary + default policy, not a journey.

## Acceptance criteria

- [x] Concepts page states `wt-native` is the **default** and describes it as a lightweight
      AC + Test plan portable that expects verification before `done`.
- [x] Outbound schemes table lists only real schemes (`wt-native`, `plain-md`) with accurate
      roles; narrative says default tries to enforce verify.
- [x] Home and concepts index link the new page; mkdocs nav includes it.
- [x] No `authxx` residue under `docs/product/` or in `docs/WORKFLOW.md`.
- [x] `python3 tools/spec_lint.py` exits 0; ledger regenerated (`--write-ledger`).

## Test plan

- **Automated tests:** N/A for prose — no runtime change intended. `python3 tools/spec_lint.py`
  + `--write-ledger`; spot-check `uv run wt spec schemes` names match docs.
- **Manual verification:** `rg authxx docs/product docs/WORKFLOW.md` empty; concepts page +
  outbound schemes reviewed; scheme names match CLI.
- **Regression guard:** no behavioral edits under `src/wt/export_schemes/` for this SPEC.

## Clock Log

CLOCK-IN: 2026-09-09T21:37:00-04:00
CLOCK-OUT: 2026-09-09T21:55:00-04:00

## Rollout / migration

Docs-only; publish with next docs site build / Pages workflow.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed.
- [x] No regressions.
- [x] Spec body matches shipped docs.
- [x] `docs/LEDGER.md` regenerated; status `done`.

## Open questions

None.
