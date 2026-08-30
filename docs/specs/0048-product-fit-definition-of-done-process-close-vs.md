---
id: SPEC-0048
title: "Outbound outcome DoD (process close vs product-fit)"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
parent: SPEC-0046
tags: [outbound, export, dod, workflow-audit]
source_idea: IDEA-034
depends_on: [SPEC-0000, SPEC-0015, SPEC-0041, SPEC-0045]
---

## Context

Promoted from `IDEA-034` (epic SPEC-0046). AGENTS.md Definition of Done is correct for an
internal CLI (AC + Test plan + ledger). Outbound magnifies “objectively checkable” AC into
file/CLI assertions that can pass while the product miss remains (wrong dashboard, empty
workflow). Export CLI does not even require `status: accepted` today — soft skill only.
`canonical.py` already accepts optional `outcome:` (and related) frontmatter for REMOVED.

## Goals / Non-goals

**Goals**
- Make **outbound** authxxing/export/implement guidance require product-fit signal: ≥1
  outcome-shaped Acceptance criterion (“I can …”) **or** non-empty `outcome:` frontmatter.
- Keep internal Meta-Tools process DoD unchanged.

**Non-goals**
- New `export-ready` / `product-accepted` status values in v1.
- Hard-failing every Meta-Tools internal spec on outcome wording.
- Replacing Test plans with demos.

## Decision

**Outbound-primary outcome bar, soft-to-firm:**

1. Document two AC classes in outbound-facing docs/skills: *mechanical* vs *outcome*.
2. `wt-export` and `wt-implement-spec`: refuse or loudly warn when outbound portable/outbox
   feature|epic lacks both outcome AC and `outcome:` (prefer warn-at-export skill + optional
   scheme `validate()` warning or non-zero soft check — hard fail only if cheap and reliable).
3. Prefer hard fail in REMOVED `validate()` when `outcome` empty **and** no AC bullet looks
   outcome-like (heuristic: starts with “I can” / “User can” / “Operator can”, case-insensitive)
   — document the heuristic; allow `--force` on export to bypass if needed for legacy.
4. No change to AGENTS.md internal done checklist.

## Design

- Docs: SCHEMA or WORKFLOW outbound subsection; TEMPLATE.md comment/example outcome AC.
- Skills: `wt-export`, `wt-implement-spec`, optionally `wt-new-work` when `--target`/outbound.
- Code: `REMOVED.validate` and/or shared helper `has_outcome_signal(canonical)`; wire
  export path to surface Clearmessage. wt-native may warn similarly without blocking v1 if TC
  is the high-stakes path — **both** schemes should share the helper so wt-native exports also
  get the signal.
- Tests: fixture specs with/without outcome; export validate behavior.

## Alternatives considered

- **export-ready status** — deferred (lifecycle complexity; IDEA-031 adjacent).
- **Human sign-off flag on every export** — too much ceremony; fit-log (0049) covers learning.
- **Outcome required for internal specs** — rejected; polish tax.

## Acceptance criteria

- [x] Shared helper detects outcome signal (`outcome:` or outcome-shaped AC).
- [x] Outbound export path warns or fails (documented) when signal missing; `--force` escape
      if hard-fail is chosen.
- [x] `wt-export` / `wt-implement-spec` document the outcome bar.
- [x] Internal Meta-Tools AGENTS DoD text unchanged in meaning.
- [x] Tests cover positive/negative fixtures.

## Test plan

- **Automated:** unit tests for helper; export scheme validate tests.
- **Manual:** attempt export of outcome-less outbound draft; confirm message.
- **Regression:** existing outbound fixtures with outcome/AC still export.

## Rollout / migration

Legacy outbox specs: add `outcome:` or one outcome AC on next edit; `--force` if blocked.

## Definition of done

- [x] AC met; tests green; ledger updated.

## Open questions

_Resolved: TC hard-fail via validate; wt-native stderr warn; `--force` skips outcome problems._
