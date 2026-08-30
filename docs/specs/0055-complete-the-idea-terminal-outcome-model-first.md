---
id: SPEC-0055
title: "Complete the idea terminal-outcome model (close verb, reason, pointers)"
status: accepted
owner: user
created: 2026-07-24
updated: 2026-07-24
kind: epic
milestone: "M4: cli ergonomics"
source_idea: IDEA-065
tags: [ideas, workflow, lifecycle]
---

## Context

Promoted from `IDEA-065`. The idea terminal-outcome model is incomplete and asymmetric. Ideas
have three "done" states (`PROMOTED`, `EXPORTED`, `DROPPED`), but:

- `PROMOTED`/`EXPORTED` are set automatically as pipeline side-effects (`wt spec generate` /
  `wt spec export`), reason-free.
- `DROPPED` has **no first-class path** — no verb, no reason capture; you must fall back to the
  generic `wt state IDEA-NNN DROPPED`. It exists only as a listing filter.
- There is **no** terminal outcome for "explored, no implementation needed, knowledge worth
  keeping" — the motivating case, `IDEA-062`, whose exploration collapsed to a predicate that
  belongs in `IDEA-059` plus an out-of-repo follow-up. Forcing it to `PROMOTED` yields a spec
  with an empty implementation; `DROPPED` reads as rejected and loses the signal; `INCUBATE`
  conflates it with active work.

The exploration (research root = this wt checkout) established that the state machinery is
mostly ready and located the one genuinely new piece:

- `org_write.set_state` is the sole write path; it validates against the file's `#+TODO`
  keyword set and **auto-manages the `CLOSED:` stamp** for any done-key. A new terminal keyword
  added to `org_idea_keywords` after `|` therefore inherits done-semantics, the CLOSED stamp,
  exclusion from default `wt ideas`/`wt next` (`is_done`), and reversibility (moving back to
  `INCUBATE` drops the stamp) **for free**.
- But `set_state` only rewrites the keyword + CLOSED line — it **never writes
  `:PROPERTIES:`**. Capturing a reason or a `folded_into:`/`superseded_by:` pointer needs a
  new property/Log writer. That is the new capability this epic introduces.
- `workflow.next_step_for_idea` already branches `DROPPED → ""`; each new terminal state needs
  one matching no-hint branch.

## Goals / Non-goals

**Goals**
- One generic, ergonomic way to *close* an idea with an explicit, reasoned outcome, replacing
  the verbless `wt state … DROPPED`.
- A distinct terminal state for "explored, no spec needed" so it is not conflated with
  won't-do or with active work.
- Durable pointers to where a closed idea's value went (folded into / superseded by another
  idea or spec).

**Non-goals**
- Changing how `PROMOTED`/`EXPORTED` are reached (pipeline stays automatic).
- A general org property-editing surface — only the lifecycle properties this needs.
- Building the out-of-repo sync mechanism in this epic (its shape is unknown; it is captured as
  a deferred child for its own exploration).

## Decision

Introduce a single generic verb `wt idea close IDEA-NNN --as drop|researched` that:
1. sets the matching terminal keyword — `--as drop` → `DROPPED`, `--as researched` →
   a new `RESEARCHED` keyword (the "explored, no spec" outcome), via `set_state`;
2. records a reason and optional relationship pointers through a new property/Log writer.

Distinct **keywords** carry the outcome (a reader tells won't-do from explored-no-spec at a
glance); the **reason and pointers are properties/Log**, orthogonal to the keyword. Reaching a
terminal state stays reversible via the existing `wt state … INCUBATE`.

## Architecture / cross-cutting design

- **Keyword set.** Add `RESEARCHED` to `org_idea_keywords` after `|`
  (`… | PROMOTED EXPORTED DROPPED RESEARCHED`) and to the ideas file's `#+TODO` header. It is a
  done-key, so listing/`CLOSED:`/reversibility come from `set_state` unchanged.
- **Property/Log writer (new, `org_write.py`).** A minimal, drift-guarded setter that
  adds/updates named keys in an idea's `:PROPERTIES:` drawer (e.g. `CLOSE_REASON`,
  `FOLDED_INTO`, `SUPERSEDED_BY`) and appends a dated Log line — the only new mutation
  primitive. All child specs use it; it never edits headline/tags/body.
- **`wt idea close` verb (`cli.py` + `explore.py`).** `--as [drop|researched]` (required),
  `--reason TEXT`, `--folded-into SELECTOR`, `--superseded-by SELECTOR`. Resolves the idea,
  calls `set_state` for the keyword, then the property/Log writer for reason + pointers.
- **Next-hint + surfacing.** `next_step_for_idea` returns `""` for `RESEARCHED` (as for
  `DROPPED`). `wt idea show` / `--json` surface `close_reason` and pointer links (`[[IDEA-…]]`).

## Breakdown / sub-specs

- [x] **SPEC-0056** Generic wt idea close verb + RESEARCHED state + reason — **done**.
- [x] **SPEC-0057** Relationship pointers: folded-into / superseded-by — **done**.
- [ ] Out-of-repo follow-up parking (**deferred**, tracked as `IDEA-068`) — park an action
  owned by another repo when closing an idea; likely a new one-way incremental sync capability
  wt lacks today. Shape unknown — stays an idea for its own `/wt-explore` before it earns a
  spec. Not required for the epic's core value.

Sequencing / dependencies: first child is the foundation (verb + writer + state); the pointers
child builds on it; the out-of-repo child is independent and deferred pending exploration.

## Acceptance criteria

- [ ] `wt idea close IDEA-NNN --as drop --reason "…"` sets `DROPPED`, a `CLOSED:` stamp, a
      `CLOSE_REASON` property, and a Log line — in one command.
- [ ] `wt idea close IDEA-NNN --as researched --reason "…" --folded-into IDEA-MMM` sets a new
      `RESEARCHED` terminal state and records the `FOLDED_INTO` pointer + cross-link.
- [ ] `RESEARCHED` ideas are excluded from default `wt ideas`/`wt next` and yield no next-step
      hint; they remain visible under `--all` and in `wt idea show`.
- [ ] A closed idea can be reopened (`wt state IDEA-NNN INCUBATE`) with the `CLOSED:` stamp
      removed (existing behavior, unbroken).
- [ ] `wt idea show`/`--json` surface the close reason and any folded-into / superseded-by
      pointer.

## Test plan

- **Integration/e2e tests:** drive `wt idea close` through both `--as` modes end-to-end and
  assert the resulting org (keyword, CLOSED stamp, properties, Log) and the `wt ideas`/`wt
  next`/`wt idea show` views; confirm reopen. Per-unit coverage (property writer, keyword
  parsing) lives in each child spec.
- **Manual verification:** close `IDEA-062` as `researched --folded-into IDEA-059`; confirm it
  drops out of `wt next`, still shows with its reason + link, and `IDEA-059` is referenced.
- **Regression guard:** full `uv run pytest` green; `PROMOTED`/`EXPORTED` paths and existing
  `wt state` behavior unchanged.

## Rollout / sequencing

1. First child (close verb + `RESEARCHED` + reason writer) — the foundation.
2. Pointers child on top.
3. Out-of-repo child stays an INCUBATE idea until explored; not required for the epic's core
   value.

## Definition of done

- [ ] All child specs `done` or `superseded` (the linter gates this).
- [ ] Integration test plan executed; `uv run pytest` green.
- [ ] Acceptance criteria met; epic body reflects what shipped.
- [ ] `docs/LEDGER.md` regenerated.

## Open questions

- Terminal-state name `RESEARCHED` vs `ARCHIVED` — either is acceptable (owner indifferent);
  `RESEARCHED` chosen for specificity. Confirm before the first child is accepted.
- Whether the out-of-repo child is ever built here or spun into a standalone epic once its
  one-way-sync shape is explored.
