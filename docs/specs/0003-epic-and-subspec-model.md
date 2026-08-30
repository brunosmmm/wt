---
id: SPEC-0003
title: Epic & sub-spec model
status: done
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M0: process"
kind: feature
tags: [process, tooling]
depends_on: [SPEC-0000, SPEC-0002]
---

## Context

The spec system ([SPEC-0000](./0000-how-we-write-specs.md)) models a *flat* list of specs
with only `depends_on`. A large, complex feature can't be captured in one spec — it fans
out into many sub-specs that must be planned together and driven to completion as a unit.
We need a hierarchy primitive (an **epic** with **child** specs) and a ledger that *rolls
up* child progress instead of listing flat rows that drift out of date as specs multiply.

## Goals / Non-goals

**Goals**
- A first-class way to express "this large feature = these N sub-specs."
- A ledger that shows epic progress (`3/8 done`) and stays in sync automatically.
- Kind-aware lint rules so epics/policy/spike specs are held to the right bar.

**Non-goals**
- Auto-deriving epic status (authxx sets it; the linter only *gates* it).
- Hierarchical ids or per-epic subdirectories (decided against — flat ids + `parent`).
- A full project-management tool; this is lightweight planning metadata.

## Decision

Add two optional frontmatter fields — `kind` (`feature`|`epic`|`policy`|`spike`, absent =
`feature`) and `parent` (the epic a child belongs to). Hierarchy's single source of truth
is the child's `parent`; the tree is *derived*. The ledger's spec index becomes a
**generated artifact** produced by the SPEC-0002 linter (`--write-ledger`), including an
Epics rollup. Kind drives lint rules (below).

## Design

### Frontmatter (schema)

- `kind`: enum `[feature, epic, policy, spike]`, optional (absent ⇒ `feature`).
- `parent`: `SPEC-NNNN`, optional. Present only on children.
- Ids stay flat and sequential; specs stay in `docs/specs/` (no subdirs).

### Epic authxxing

New `TEMPLATE-epic.md` with epic-shaped sections: *Architecture / cross-cutting design*,
**Breakdown / sub-specs** (the child checklist + sequencing), and an **Integration test
plan** (the epic's test plan is end-to-end, not unit). A child spec sets `parent:` and is
otherwise a normal feature spec.

### Linter rules (extending SPEC-0002's `tools/spec_lint.py`)

Adds to the existing checks:
- **parent integrity:** `parent` resolves to an existing spec whose `kind` is `epic`.
- **epic completion gating:** an `epic` with `status: done` requires every child
  (`parent == epic.id`) to be `done` or `superseded`.
- **kind-aware test plan:** `feature`/`epic` require a non-empty Test plan; `policy`/`spike`
  may use `N/A — <reason>`.

### Generated ledger

`docs/LEDGER.md` keeps a hand-written header and Milestones section; the spec index lives
in a generated block between `<!-- specs:begin -->` / `<!-- specs:end -->` markers:
- **Epics** rollup: per epic, `status (x/y children done)` + a child checklist.
- **Active & planned**, **Done**, **Superseded / rejected** tables.

`python3 tools/spec_lint.py --write-ledger` regenerates the block. The default lint run
*verifies* the block is current (fails with "run --write-ledger" if stale), which replaces
the old ad-hoc ledger-status check — drift becomes impossible to miss.

## Alternatives considered

- **Hierarchical ids (SPEC-0003.2) / per-epic subdirs** — rejected (breaks the 4-digit id
  pattern & sorting; adds filesystem ceremony) in favor of flat ids + `parent`.
- **Hand-maintained Epics section** — rejected; generation from frontmatter eliminates
  drift as spec count grows.
- **Auto-derived epic status** — rejected; explicit status + a done-gate is simpler and
  keeps the authxx in control.

## Acceptance criteria

- [x] Schema accepts `kind` + `parent` (and still rejects unknown keys — `additionalProperties: false`).
- [x] `TEMPLATE-epic.md` exists; `SCHEMA.md` documents `kind`, `parent`, and epic sections.
- [x] Linter enforces parent integrity, epic done-gating, and kind-aware test-plan rules,
      each demonstrated firing on the 9-violation negative fixture.
- [x] `tools/spec_lint.py --write-ledger` generates the Epics rollup + tables; a plain lint
      run fails when `LEDGER.md`'s generated block is stale (verified).
- [x] `python3 tools/spec_lint.py` exits 0 on the current `docs/specs/` with a generated,
      up-to-date ledger.

## Test plan

- **Automated (done):** covered by SPEC-0002's `tests/test_specs.py` (runs the linter over
  `docs/specs/` and asserts no problems). `uv run pytest` → 12 passed.
- **Manual verification (done):** ran `tools/spec_lint.py --write-ledger` and confirmed the
  Epics rollup + tables render; a 9-violation negative fixture confirmed parent-not-epic,
  epic-done-with-open-child, kind-aware N/A-test-plan, and stale-ledger all fire with a
  non-zero exit.
- **Regression guard:** the linter runs over all specs every time (via pytest), so the new
  rules guard every future spec.

**Deviation:** the negative fixture was exercised manually (a throwaway temp tree), not
committed as a test; the committed `test_specs.py` asserts the positive (all real specs
pass). Enough to guard regressions without shipping deliberately-broken specs in the repo.

## Rollout / migration

1. Schema + `kind` on existing specs (0000 policy, 0001/0002 feature).
2. Rewrite `tools/spec_lint.py` with the new checks + `--write-ledger`.
3. Add markers to `LEDGER.md`; generate the block.
4. `TEMPLATE-epic.md` + `SCHEMA.md` docs.
5. Finish SPEC-0002 (pytest wiring + `wt spec lint`) so the linter is enforced in CI/tests.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green (12 passed); manual verification performed.
- [x] Spec body reflects what shipped (incl. deviations).
- [x] `docs/LEDGER.md` regenerated and shows this spec.

## Open questions

_None._
