---
id: SPEC-0045
title: "Global wt-implement-spec skill for exported portable specs"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
tags: [skills, export, outbound, ergonomics]
source_idea: IDEA-056
depends_on: [SPEC-0015, SPEC-0017, SPEC-0041]
---

## Context

Promoted from `IDEA-056`. After exporting outbound specs into a target repo, a bare agent
told only “implement” freestyles. Export already drops a thin `.contract.md`, but nothing
gave a discoverable procedure without rigidifying the target’s `AGENTS.md`. `wt skills
install` already publishes playbooks globally into `~/.claude/skills/`.

## Goals / Non-goals

**Goals**
- Global `wt-implement-spec` skill; contract pointer; no target AGENTS.md splice.

**Non-goals**
- Per-export skill drop; dual Cursor default dest; portable status semantic changes.

## Decision

Ship `wt-implement-spec` via SPEC-0017 install; point wt-native contracts at it.

## Design

### Skill
`skills/wt-implement-spec/SKILL.md` — resolve portable spec → `in-progress` → implement →
Test plan → AC → `done`; never `wt spec generate` on outbound; optional `pull-status` note.

### Contract
`wt_native._render_contract` leads with `/wt-implement-spec` and forbids generate.

### Docs
`docs/WORKFLOW.md`, `README.md`, `skills/wt-export` mention the skill.

## Alternatives considered

- Per-export drop / AGENTS.md splice / thicker contract only — rejected as explored.

## Acceptance criteria

- [x] `skills/wt-implement-spec/SKILL.md` exists with real procedure + outbound/generate
      guardrails.
- [x] `wt skills install --dest <tmp>` installs it; `EXPECTED_SKILLS` / list tests updated.
- [x] wt-native `.contract.md` mentions `/wt-implement-spec` (or `wt-implement-spec`).
- [x] Export tests updated and green; full pytest green.
- [x] WORKFLOW (or README) notes the skill for post-export implementation.
- [x] Skill text never directs `wt spec generate` for outbound portables.

## Test plan

- **Automated:** `tests/test_skills.py`, `tests/test_export.py`; full suite 334 passed.
- **Manual:** `wt skills install` linked `wt-implement-spec`.
- **Regression:** other skills/export paths green.

## Rollout / migration

Re-`wt skills install` on authxx machines (done here). Re-export outbound specs when you want
refreshed contracts in target repos.

## Definition of done

- [x] AC met; tests green; ledger current; skill installable globally.

## Open questions

_None._
