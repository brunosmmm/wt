---
id: SPEC-0024
title: Formal explore stage + wt-explore skill
status: done
owner: user
created: 2026-07-22
updated: 2026-07-22
milestone: "M4: cli ergonomics"
kind: feature
tags: [ideas, skills, ergonomics, workflow]
source_idea: IDEA-011
depends_on: [SPEC-0012, SPEC-0013, SPEC-0017, SPEC-0023]
---

## Context

Promoted from idea `IDEA-011` (formal explore stage before promotion).

The idea→spec pipeline jumped from capture to promotion, skipping durable exploration.
Free chat loses knowledge; `wt-new-work` promoted too early. This spec adds the missing
explore stage.

## Goals / Non-goals

**Goals**
- Capture → **explore (durable)** → decide → promote/authxx → accept → generate → build.
- Idea enrichment: Summary / Open questions / Log on the org subtree.
- CLI + `wt-explore` skill; narrowed `wt-new-work`; next-step explore-before-promote.
- WORKFLOW.md / README / related skills updated.

**Non-goals**
- Replacing free chat; changing `wt-generate`; hard-fail promote; new EXPLORED TODO state.

## Decision

Org subtree sections as system of record; `wt idea explore|summary|questions|retitle|show`;
`IdeaGroup` keeps bare `wt idea TEXT` as capture; `wt-explore` never promotes; `wt-new-work`
gates on Summary; `next_step_for_idea` and `wt spec new` warn/guide explore-first.

## Design

### CLI

`wt idea` is an `IdeaGroup`: unknown first token → `capture`; known subcommands → explore
path. Helpers in `src/wt/explore.py`.

### Skills

`skills/wt-explore/`; rewritten `wt-new-work`, `wt-capture`, `wt-orient`.

### next_step / promote warn

Empty Summary → `wt idea explore {id}`; non-empty → `wt spec new --from-idea {id}`.
`scaffold_from_idea` / `scaffold_outbound` warn on empty Summary unless `--force`.

## Alternatives considered

As accepted: design-note primary store rejected; EXPLORED state deferred; hard-fail promote
deferred; in-chat-only explore rejected.

## Acceptance criteria

- [x] Idea subtree conventions + CLI create/update; `wt idea show` prints them.
- [x] Subcommands never promote; `wt idea explore` never captures an idea titled `explore …`.
- [x] `skills/wt-explore/SKILL.md` installable; forbids promote/generate.
- [x] `wt-new-work` post-explore + Summary gate; capture/orient updated; skills list includes
      `wt-explore`.
- [x] `next_step_for_idea` explore vs promote by Summary.
- [x] `wt spec new --from-idea` warns when Summary empty (unless `--force`).
- [x] WORKFLOW.md + README describe capture → explore → …
- [x] Promotion Context includes Summary/Log (`tests/test_explore.py`).
- [x] `uv run pytest` → 245 passed; skills tests include `wt-explore`.

## Test plan

- **Automated:** `tests/test_explore.py` + updated workflow/skills/ideas tests. ✓
- **Manual:** CLI smoke capture/explore/summary/show/next. ✓
- **Regression:** 245 passed.

## Rollout / migration

Shipped. Old ideas with empty Summary get explore hints from `wt next`. Re-run
`wt skills install` to pick up `wt-explore`.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` → 245 passed.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` updated.

## Open questions

_None._
