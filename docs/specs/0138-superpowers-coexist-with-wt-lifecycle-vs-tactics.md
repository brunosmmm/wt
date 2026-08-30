---
id: SPEC-0138
title: "Superpowers coexist with wt: lifecycle vs tactics"
status: done
owner: user
created: 2026-08-30
updated: 2026-08-30
source_idea: IDEA-312
kind: feature
milestone: "M4: cli ergonomics"
tags: [skills, orient, ergonomics, agents]
depends_on: [SPEC-0017, SPEC-0051, SPEC-0095, SPEC-0117, SPEC-0137]
---

## Context

Promoted from `IDEA-312`. Cursor may load Claude's **Superpowers** plugin via a session
hook even when the chat model is not Claude Code, steering agents into
`docs/superpowers/**` and past wt's idea→verify loop (DemoBrew transcript evidence).

## Goals / Non-goals

**Goals** — Document coexistence; update orient + related skills + AGENTS/WORKFLOW; skill-level
hard gate; forbid governing `docs/superpowers/**` when wt is in play.

**Non-goals** — Disabling Superpowers; patching upstream Superpowers; tool-level Write blocks;
DemoBrew doc migration.

## Decision

Shipped as designed: wt owns lifecycle + governing design; Superpowers is tactical inside an
authxxized slice; `/wt-verify` required to claim done; "just build"/"keep working" → hub/next.

## Design

- `skills/wt-orient` — **Coexistence with Superpowers** subsection (table, gate, path forbid).
- Cross-links in `wt-seed`, `wt-explore`, `wt-new-work`, `wt-implement-spec`, `wt-verify`.
- `AGENTS.md` — Agent skill priority; `docs/WORKFLOW.md` — short pointer.
- Regression: `tests/test_skills.py::test_superpowers_coexistence_guidance_spec_0138`.

## Acceptance criteria

- [x] `wt-orient` documents coexistence (table, path forbid, hard gate, hub/next).
- [x] seed / explore / new-work point away from governing Superpowers paths.
- [x] implement-spec / verify require wt verify (not Superpowers-only) to claim done.
- [x] `AGENTS.md` states skill priority.
- [x] `python3 tools/spec_lint.py` exits 0; skill-text test passes.

## Test plan

Executed: `uv run pytest tests/test_skills.py` (includes SPEC-0138 coexistence test).

## Definition of done

- [x] AC met; test plan executed; body matches ship; ledger updated.

## Open questions

_(none)_
