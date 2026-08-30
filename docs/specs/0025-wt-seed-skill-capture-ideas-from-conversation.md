---
id: SPEC-0025
title: "wt-seed skill: capture ideas from conversation context"
status: done
owner: user
created: 2026-07-22
updated: 2026-07-22
milestone: "M4: cli ergonomics"
kind: feature
tags: [skills, ideas, ergonomics, workflow]
source_idea: IDEA-012
depends_on: [SPEC-0017, SPEC-0024]
---

## Context

Promoted from idea `IDEA-012` (wt-seed skill).

`wt-capture` parks a **user-supplied one-liner**. After a long design chat, there is no
playbook that distills **already-discussed conversation** into a durable idea (title +
optional Summary / Open questions / Log). Free chat loses that synthesis; agents either
skip capture or paste a thin title and leave enrichment empty.

Prior art: claude-brain `/brain-digest init` (“Draft it for me from context”, optional
context/scope, bootstrap from existing artifacts). That maps onto **wt ideas**, not branch
digests — reuse explore CLI writes from [SPEC-0024](./0024-formal-explore-stage-wt-explore-skill.md),
not a new digest store.

## Goals / Non-goals

**Goals**
- Ship **`wt-seed`**: conversation → durable idea (inverse of `wt-capture`: thought → idea).
- Skill-only v1: compose existing `wt idea` / `summary` / `questions` / `explore` / `show`.
- Preview title (+ proposed enrichment) before write; never promote or generate.
- Cross-link capture / explore / orient / WORKFLOW so agents pick the right entry skill.

**Non-goals**
- New CLI (`wt idea seed`) in v1.
- Branch create, scope checklists, tracking links, or brain-digest lifecycle (`update` /
  `compact` / `close`).
- Merging seed into `wt-capture` (distinct triggers).
- Hard-requiring a Summary (title-only seed remains valid when chat was thin).
- Changing promote / next-step rules beyond skill docs.

## Decision

Add repo skill `skills/wt-seed/SKILL.md`, installable via `wt skills install`. It synthesizes
the current conversation (or an `$ARGUMENTS` topic slice) into a short title, previews the
draft for confirmation, then writes with existing CLI — preferring `--state INCUBATE` when
also seeding enrichment. Enrichment is **recommended** when the chat already did
explore-quality thinking, but **optional**. The skill never runs `wt spec new` or
`wt spec generate`. Keep `wt-capture` for stray one-liners; keep `wt-explore` for
post-capture research on an existing id.

## Design

### Skill procedure

1. **Confirm intent** — seed from this conversation, or the topic named in `$ARGUMENTS`.
2. **Draft** — one-sentence title; optional `--project` / `--tag` / `--priority` inferred
   only from explicit cues in the chat (do not invent associations).
3. **Preview** — show proposed title, flags, and any Summary / questions / Log notes; wait
   for confirm or edit. No silent write.
4. **Capture** — `wt idea "<title>"` with chosen flags; use `--state INCUBATE` when step 5
   will write enrichment.
5. **Optionally enrich** — `wt idea summary <ID> --set "…"`, `questions …`, one or more
   `explore <ID> --note "…"` drawn only from decisions/findings already present in the
   conversation (no invented work).
6. **Stop** — `wt idea show <ID>`; point at `wt next` / `/wt-explore` / `/wt-new-work` as
   appropriate. Never promote.

### Guardrails (in the skill body)

- Do not invent requirements or scope not present in the conversation.
- Prefer short titles; put substance in Summary / Log.
- Never hardcode flag lists — point at `wt idea --help` / subcommand `--help`.
- Never promote or generate.

### Docs / sibling skills

- `docs/WORKFLOW.md` + README: add `wt-seed`; fix stale “no `wt idea show`” claim.
- `wt-capture` / `wt-orient` / `wt-explore` cross-link `wt-seed`.

### Tests

- `tests/test_skills.py` expects seven skills including `wt-seed`.

## Alternatives considered

- **Fold into `wt-capture`** — lost: different triggers; rejected.
- **New `wt idea seed` CLI** — deferred.
- **Fire-and-forget without preview** — rejected.
- **Require non-empty Summary** — rejected (optional).
- **Port full brain-digest** — rejected.

## Acceptance criteria

- [x] `skills/wt-seed/SKILL.md` exists with name/description/trigger; procedure matches Design;
      forbids promote/generate; defers flags to `--help`.
- [x] `wt skills install` / `wt skills list` include `wt-seed`; `tests/test_skills.py` expects
      it alongside the existing skills.
- [x] `wt-capture`, `wt-orient`, and `wt-explore` cross-link `wt-seed` where appropriate.
- [x] `docs/WORKFLOW.md` documents `wt-seed`; removes the stale “no `wt idea show`” claim;
      README skill list updated.
- [x] No new CLI surface required for this spec.
- [x] `uv run pytest` passes (skills tests + full suite).

## Test plan

- **Automated:** `tests/test_skills.py` inventory + thinness; full `uv run pytest`. ✓
- **Manual:** `wt skills install --dest <tmp>` linked `wt-seed`. ✓
- **Regression:** capture/explore/new-work thinness unchanged; no CLI changes. ✓

## Rollout / migration

Shipped. Re-run `wt skills install` (or `--force`) to pick up `wt-seed`. No data migration.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green; manual install check done.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated (`python3 tools/spec_lint.py --write-ledger`).

## Open questions

_None._
