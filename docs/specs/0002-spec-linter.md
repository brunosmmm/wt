---
id: SPEC-0002
title: Spec linter
status: done
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M0: process"
kind: feature
tags: [process, tooling]
depends_on: [SPEC-0000]
---

## Context

[SPEC-0000](./0000-how-we-write-specs.md) sets content rules and a loop-closure bar. Prose
alone drifts; we want the mechanical parts enforced automatically so a `done` spec can't
lie about being tested and a malformed spec is caught immediately.

## Goals / Non-goals

**Goals**
- One command that validates every spec's frontmatter and the checkable content rules.
- Usable **now** (before the `wt` package exists) and later wired into the package + tests.

**Non-goals**
- Judging prose quality or semantic correctness (that's for review).
- Blocking CI infrastructure setup (out of scope; runs locally / in `pytest`).

## Decision

Ship a standalone `tools/spec_lint.py` as the source of truth and enforce it in `pytest`
(`tests/test_specs.py` runs it over `docs/specs/`). The checks below are the contract.

**Decision (deviation from the original sketch):** the linter is a **repo dev tool**, not a
`wt` subcommand. Linting specs is a development/CI activity; exposing it through the
time-tracking CLI would conflate the two and wouldn't work for a globally-installed `wt`
(which has no `tools/` alongside it). It runs via `python3 tools/spec_lint.py` and is
enforced by `uv run pytest`. (Check-set later extended by
[SPEC-0003](./0003-epic-and-subspec-model.md): parent integrity, epic gating, kind-aware
test plan, generated ledger.)

## Design

`tools/spec_lint.py` scans `docs/specs/NNNN-*.md` (skipping `TEMPLATE.md`) and reports all
violations, exiting non-zero if any. Checks:

1. **Frontmatter parses** and validates against `spec.schema.json` (dates normalized to ISO
   strings before validation, since YAML parses them to `date` objects).
2. **`id` matches filename** — `SPEC-000N` ↔ `000N-slug.md`.
3. **Required body sections present:** `## Context`, `## Decision`, `## Acceptance
   criteria`, `## Test plan`, `## Definition of done`.
4. **Test plan non-empty.** For feature specs it must have real content; `N/A — <reason>`
   is accepted (policy/doc escape hatch per SPEC-0000).
5. **`done` specs are closed:** no unchecked `- [ ]` boxes remain under *Acceptance
   criteria* or *Definition of done*.
6. **Reference integrity:** every id in `supersedes` / `depends_on` / `superseded_by`
   resolves to an existing spec file.
7. **Ledger consistency:** every spec appears in `docs/LEDGER.md` and its status there
   matches the frontmatter.

## Alternatives considered

- **Put the linter only in the `wt` package** — cleaner long-term but unavailable until
  SPEC-0001 lands; we want enforcement immediately. Chosen: standalone now, integrate later.

## Acceptance criteria

- [x] `python3 tools/spec_lint.py` exits 0 on the current `docs/specs/` and prints a clean
      summary.
- [x] Each check fires on a deliberately broken spec and is reported with the file and
      reason (demonstrated across a 9-violation negative fixture).
- [x] Exit code is non-zero when any violation exists.

## Test plan

- **Automated (done):** `tests/test_specs.py` loads the linter and asserts
  `validate(load_specs())` is empty over the real `docs/specs/` — so `uv run pytest` fails
  if any spec (or the ledger) drifts. (`uv run pytest` → 12 passed.)
- **Manual verification (done):** ran `python3 tools/spec_lint.py` (exit 0 on all specs);
  built a 9-violation negative fixture and confirmed every check fires with a non-zero
  exit. A dedicated `--selftest` mode was not added — the negative fixture + the pytest
  gate cover it.
- **Regression guard:** the linter runs over all specs, so any future spec that breaks the
  rules fails `pytest`.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green (12 passed); negative fixture verified.
- [x] `docs/LEDGER.md` regenerated (status `done` + date).

## Open questions

_Deferred (advisory, not blocking):_ enforcing that `depends_on` targets are `accepted`+
before a dependent reaches `in-progress`. Not implemented — revisit if it proves useful.
