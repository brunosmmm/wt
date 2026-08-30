---
id: SPEC-0000
title: How we write & execute specs
status: accepted
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M0: process"
kind: policy
tags: [process]
---

## Context

This project is developed spec-first (see [`AGENTS.md`](../../AGENTS.md)). The
[schema](./spec.schema.json) makes *frontmatter* machine-checkable, but it cannot express
what makes a spec *good*: clear scope, checkable criteria, and — critically — a real plan
for how the change will be tested and how the authxx will **close the loop** before calling
it done. This spec is the lean layer that carries those rules. It is intentionally short;
if it grows into process bureaucracy, trim it.

## Goals / Non-goals

**Goals**
- Reinforce schema adherence with a small set of content rules a schema can't capture.
- Make a **test plan** a first-class, expected part of every feature spec.
- Make **loop closure** (tests executed, acceptance met, spec kept truthful) the bar for
  `done`, and enforce it with tooling.

**Non-goals**
- Heavyweight process. One decision per spec; prefer superseding over sprawling.
- Replacing `AGENTS.md` — that stays the short operational contract; this is the rationale
  and authxxing guidance behind it.

## Decision

Every spec follows the schema **and** these content rules, and no spec is marked `done`
until its loop is closed. An automated linter ([SPEC-0002](./0002-spec-linter.md)) enforces
the mechanical parts.

## Design

### Content rules (beyond the schema)

- **Context** states the problem and what exists today — not the solution.
- **Goals / Non-goals** are explicit; non-goals prevent scope creep.
- **Decision** is stated as a decision (imperative), not a discussion.
- **Acceptance criteria** are *objectively checkable*. "Works well" is not a criterion;
  "`wt report -w` output is byte-identical to the baseline" is.
- **Alternatives considered** names at least what was rejected and why.
- **One decision per spec.** Split unrelated concerns into separate specs; link with
  `depends_on`.

### Test-plan requirement

- **Feature/behavior specs MUST include a non-empty Test plan** covering: automated tests
  (what & where), manual verification (commands + expected result), and a regression guard.
- **Pure policy/doc specs** (like this one) may write `N/A — <reason>` for the test plan.
- A feature spec without a test plan is *incomplete* and must not reach `accepted`.

### Loop closure / Definition of Done

A spec reaches `done` only when the full Definition-of-Done checklist in
[`AGENTS.md`](../../AGENTS.md) is satisfied — in particular the **test plan has actually
been executed** (`uv run pytest` green + manual steps done), the spec body reflects what
shipped, and the ledger is updated. Closing the loop on testing is non-negotiable.

### Sizing guidance (keep it lean)

Aim for one to two pages. Detail belongs in the code and tests; the spec captures the
*decision and the plan*, not an essay. When a decision changes, **supersede** — don't
rewrite history.

### Numbering

Zero-padded four digits, sequential. `SPEC-0000` is reserved for this meta-spec. The `id`
must match the filename number.

## Alternatives considered

- **A plain guideline doc (not a spec)** — simpler, but wouldn't dogfood the system or be
  supersedable through the normal flow. Rejected.
- **Folding this into `SCHEMA.md`** — leanest, but mixes machine-schema reference with
  authxxing philosophy. Rejected in favor of a dedicated, dogfooded spec.

## Acceptance criteria

- [x] Content rules, test-plan requirement, and loop-closure bar are documented here.
- [x] `TEMPLATE.md`, `SCHEMA.md`, and `AGENTS.md` are consistent with these rules.
- [x] Enforcement is specced ([SPEC-0002](./0002-spec-linter.md)).

## Test plan

N/A — policy spec. Verified by review and, mechanically, by the SPEC-0002 linter running
over `docs/specs/` (this file must pass its own rules).

## Definition of done

- [x] Rules documented and consistent across the docs system.
- [x] Linter spec exists to enforce the mechanical parts.

## Open questions

_None._
