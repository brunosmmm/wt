---
id: SPEC-0049
title: "Post-export / post-ship fit log (durable used-it miss/fit)"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
parent: SPEC-0046
tags: [outbound, export, explore, workflow-audit]
source_idea: IDEA-040
depends_on: [SPEC-0024, SPEC-0031, SPEC-0041, SPEC-0048]
---

## Context

Promoted from `IDEA-040` (epic SPEC-0046). After export/implement, nothing forces a “we used
it; here’s the miss” note. Supersede preserves design history but Explore does not get a
durable fit signal unless someone remembers `wt idea log`. SPEC-0041 deferred product-fit /
post-ship learning to this cluster.

## Goals / Non-goals

**Goals**
- Durable fit/miss notes on the **source idea** Log.
- Thin CLI: `wt spec fit-log <OUTBOUND-ID> --note "…"` resolving linked `source_idea` (or
  idea with `:SPEC:` matching the id) and appending via existing `append_log`.
- Skills tell agents to fit-log after real use or before supersede.

**Non-goals**
- Mandatory `--ack` on every `wt spec export` (ceremony).
- New org section type beyond Log.
- Auto-prompting humans in CI.

## Decision

Primary store = idea **Log**. Add `wt spec fit-log` as a convenience over `wt idea log` that
finds the idea from an outbound id. Optionally append a one-line reference to outbox
`PROVENANCE.md` (same note truncated) — nice-to-have if cheap; not required for AC.

Document in `wt-export`, `wt-implement-spec`, and `/wt-rework`: before superseding an outbound
miss, run fit-log (or idea log) with what was wrong.

## Design

- CLI: `wt spec fit-log OUTBOUND_ID --note TEXT` under `spec` group.
- Resolve idea: scan ideas for `properties.SPEC == id` or outbox frontmatter `source_idea`
  then resolve selector.
- Call `explore.append_log` (INCUBATE promotion rules as today if somehow still IDEA).
- Prefix note with a clear tag, e.g. `fit-log:` or `Post-ship fit:`, so triage can grep.
- Skills: one bullet each.
- Tests: tmp ideas file + outbox stub → fit-log → Log contains note.

## Alternatives considered

- **Only document idea log** — zero code; too easy to skip; CLI makes the habit greppable.
- **New spec section** — outbound not ledger-linted; idea Log already feeds explore.
- **Mandatory export --note** — rejected as ceremony.

## Acceptance criteria

- [x] `wt spec fit-log <OUTBOUND-ID> --note "…"` appends to the linked idea’s Log.
- [x] Errors clearly when no linked idea / outbound id missing.
- [x] Skills (`wt-export` and/or `wt-implement-spec`, `wt-rework`) mention fit-log.
- [x] Tests cover happy path + missing idea.
- [x] Export itself does not require a note.

## Test plan

- **Automated:** `tests/test_fit_log.py` (or extend export/explore tests).
- **Manual:** fit-log against a real EXPORTED idea id; `wt idea show` shows entry.
- **Regression:** `wt idea log` behavior unchanged.

## Rollout / migration

None. Optional backfill: humans fit-log on known misses anytime.

## Definition of done

- [x] AC met; tests green; ledger updated.

## Open questions

_None._
