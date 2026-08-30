---
id: SPEC-0060
title: "Agent clock-in/clock-out for wt-tracked work (org + markdown, reconciled)"
status: done
owner: user
created: 2026-07-25
updated: 2026-07-25
source_idea: IDEA-072
kind: epic
milestone: "M4: cli ergonomics"
tags: [time-tracking, guidance, org, export]
---

## Context

Promoted from `IDEA-072`. wt's aggregation (`aggregate.build`) derives seconds only from
Claude/Cursor transcript streams and meetings; `wt override` only relabels existing tracked
time. There is no supplemental, agent-driven time input today. Meanwhile, agents already drive
wt's own idea→spec→generate→implement pipeline (internal, org-tracked) and its exported
portable-spec pipeline (external, markdown-tracked in a foreign repo) — neither records the
wall-time an agent actually spends.

Exploration (research root = this wt checkout) established:
- Org clocking is half-ready: orgparse already parses `CLOCK: [start]--[end] => H:MM` entries
  under a headline's `:LOGBOOK:` drawer into `node.clock` (verified against a scratch file),
  but wt's `org.py`/`org_write.py` have zero clock reader or writer of their own.
- An agent implementing an exported portable spec in a **foreign** repo has no access to the
  wt user's org files (`wt-implement-spec`'s existing guardrail: "no wt ledger in this repo").
  So "simultaneous" clock-in on both sides is not literally executable by one process — the
  real shape is **eventual reconciliation**, mirroring the existing `wt spec pull_status`
  pattern (SPEC-0041): the portable spec already carries `source_idea:` when scaffolded from
  an idea, so a later wt-side pull can use that link.

## Goals / Non-goals

**Goals**
- An org-native clock-in/clock-out primitive for internal, org-tracked work.
- A markdown-native `## Clock Log` convention for portable specs, with guidance (in
  `wt-implement-spec` and this repo's `AGENTS.md`) telling agents to use both.
- A `wt spec pull-clock` command that reconciles a portable spec's markdown clock log into
  `CLOCK:` entries on the linked org idea (via `source_idea`).
- Clock-derived hours surfaced in `wt digest`/`wt report` as a clearly labeled **supplemental**
  source, never silently merged into passive transcript-derived totals.

**Non-goals**
- Replacing or altering the existing passive transcript/meeting aggregation
  (`aggregate.build`) — clocking is additive, surfaced separately.
- Automatic, unattended clock-in/out (e.g. hooked into every tool call) — this is an explicit
  agent action per the guidance, not instrumentation.
- Reconciling clock time for outbound specs with **no** `source_idea` link — those simply have
  no org-side reconciliation target; the markdown log still exists and is still useful on its
  own.
- Cross-machine/cross-session sync of the portable spec file itself (SPEC-0015's existing
  Non-goals already rule out live sync; `pull-clock` reads whatever local copy `wt spec
  pull-status` already assumes exists).

## Decision

Two clock conventions, one reconciliation bridge: org-native `CLOCK:` entries for internal
org-tracked work, a plain-text `## Clock Log` section for portable markdown specs, and a new
`wt spec pull-clock` command that reads the latter and writes the former onto the linked idea
(via `source_idea`) — never merging the result into wt's existing passive aggregation, only
surfacing it as a separate, labeled supplemental figure.

## Architecture / cross-cutting design

- **Org clock shape:** standard org `CLOCK: [YYYY-MM-DD Day HH:MM]--[YYYY-MM-DD Day HH:MM] =>
  H:MM` lines inside a `:LOGBOOK:` drawer immediately under the headline (org convention;
  orgparse-native). Read via `node.clock`; written by a new, drift-guarded primitive analogous
  to `set_state`/`set_property`.
- **Markdown clock shape:** a `## Clock Log` body section, plain lines `CLOCK-IN:
  [ISO timestamp]` / `CLOCK-OUT: [ISO timestamp]`, one pair per work session — human-readable,
  diffable, no frontmatter growth.
- **Reconciliation contract:** `wt spec pull-clock <OUTBOUND-ID>` reads the (local) portable
  spec's `## Clock Log`, resolves the linked idea via the outbox copy's `source_idea`
  frontmatter, and writes matching `CLOCK:` entries onto that idea's `:LOGBOOK:` — idempotent
  (a clock pair already present is not re-added).
- **Aggregation contract:** clock-derived seconds are a distinct, labeled entry in
  `wt digest`/`wt report` output (not unioned into `day_topic`/passive totals) — child 3 owns
  the exact surfacing shape.
- Each child sets `parent: SPEC-0060`.

## Breakdown / sub-specs

- [x] **SPEC-0061** Org-side clock-in/clock-out primitive — **done**.
- [x] **SPEC-0062** Markdown Clock Log convention and guidance — **done**.
- [x] **SPEC-0063** wt spec pull-clock reconciliation and supplemental aggregation — **done**.

Sequencing / dependencies: child 1 (org primitive) is independent and ships first — it is
useful standalone for any internal org-tracked work today. Child 2 (markdown convention +
guidance) can land in parallel with child 1. Child 3 (reconciliation) depends on child 2's
`## Clock Log` shape existing to parse against.

## Acceptance criteria

- [x] An agent can clock in/out on an internal org idea using a wt command, producing a
      standard `CLOCK:` entry orgparse can read back.
- [x] A newly scaffolded internal or outbound spec includes an (empty) `## Clock Log` section
      by default.
- [x] `wt-implement-spec` and this repo's `AGENTS.md` instruct agents to clock in/out during
      implementation work, in the appropriate format for each context.
- [x] `wt spec pull-clock <ID>` reads a portable spec's `## Clock Log` and writes matching
      `CLOCK:` entries onto the linked idea (via `source_idea`), without duplicating entries
      already reconciled on a prior run.
- [x] Clock-derived hours appear in `wt digest`/`wt report` as a labeled supplemental figure,
      distinct from passive transcript-derived totals.

## Test plan

- **Integration/e2e tests:** clock in/out on a fixture idea end-to-end (CLI → org file → read
  back via `Task.clock`); scaffold a fresh internal/outbound spec and assert `## Clock Log`
  is present; authxx a portable spec with a markdown Clock Log, run `pull-clock`, assert the
  linked idea's org file gains matching `CLOCK:` entries and a second run doesn't duplicate
  them; assert `wt digest`/`wt report` output includes the supplemental clock figure separate
  from the passive total. Per-unit coverage (the org writer/reader, the pull-clock parser, the
  digest surfacing) lives in each child spec.
- **Manual verification:** clock in/out on a real scratch idea and inspect the org file;
  scaffold a spec and eyeball the Clock Log section; walk `wt-implement-spec`'s new step by
  hand against a scratch portable spec.
- **Regression guard:** full `uv run pytest` green; existing `wt digest`/`wt report` output for
  ideas/specs with no clock data is unchanged.

## Rollout / sequencing

1. Child 1 (org clock primitive) lands first — usable immediately for internal work.
2. Child 2 (markdown convention + guidance + scaffolding) lands next, independent of child 1's
   internals.
3. Child 3 (pull-clock + supplemental aggregation) lands last, once child 2's Clock Log shape
   is stable.

## Definition of done

- [x] All child specs `done` or `superseded` (the linter gates this).
- [x] Integration test plan executed; `uv run pytest` green.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

- None blocking — see the source idea's fully resolved Open questions for the design record.
