---
id: SPEC-0135
title: "SHIPPED terminal, fix outbound reconcile, force state CLI+TUI"
status: done
owner: user
created: 2026-08-28
updated: 2026-08-28
source_idea: IDEA-290
milestone: "M5: interactive desk"
tags: [ideas, workflow, lifecycle, tui]
depends_on: [SPEC-0041, SPEC-0055, SPEC-0073, SPEC-0078]
---

## Context

Promoted from `IDEA-290`. Humans could not move stuck `SPECCED` / post-export ideas to a
truthful done state from the desk; `EXPORTED` is a handoff, not “shipped”; and
`wt spec reconcile` mapped every portable `done` → `PROMOTED` (including outbound), which
contradicted [SPEC-0041](./0041-outbound-export.md)’s `EXPORTED` path.
[SPEC-0078](./0078-nothing-loops-spec-completion-back-to-the-idea-a.md) deferred a distinct
`SHIPPED` name — that deferral is revoked here by human decision.

## Goals / Non-goals

**Goals**

- New done-side keyword **`SHIPPED`**: work is finished. `EXPORTED` stays “handed off via
  export.”
- Post-export feedback: portable `done` (pull-status / sweep) and reconcile advance
  `EXPORTED` (and outbound pre-terminal + `done`) → `SHIPPED`, with archive via
  [SPEC-0073](./0073-auto-archive-terminal-ideas.md).
- Force any idea keyword from **CLI** (`wt idea state`) and **TUI** (metadata → state).
- Internal reconcile `done` → `PROMOTED` unchanged.

**Non-goals**

- Renaming `PROMOTED` / `EXPORTED`.
- Requiring `CLOSE_REASON` on force-state.
- Updating outbox portable status when forcing idea state.
- Migrating historically archived `EXPORTED` ideas.

## Decision

1. `SHIPPED` on done-side after `EXPORTED` in `org_idea_keywords`.
2. `_ARCHIVE_ON_STATES` includes `SHIPPED`.
3. `pull_status`: portable first becomes `done` + idea `EXPORTED` → `set_state(SHIPPED)`.
4. Reconcile: outbound `done` → `SHIPPED`; internal `done` → `PROMOTED`; `EXPORTED`+`done` →
   `SHIPPED`.
5. `wt idea state` + TUI `m` → `state` via `set_idea_state` / `apply_mutation("state")`.
6. `next_step_for_idea(SHIPPED) == ""`; palette `bold green`.

## Design

Shipped as decided. Key call sites: `explore.set_idea_state`, `export.pull_status`,
`specs._implied_state(..., outbound=)`, `tui` metadata field `state`.

## Acceptance criteria

- [x] Default `org_idea_keywords` include `SHIPPED` after `EXPORTED`.
- [x] `set_state` to `SHIPPED` archives.
- [x] `pull_status` done + `EXPORTED` → `SHIPPED`.
- [x] Reconcile outbound/EXPORTED done → `SHIPPED`; internal done → `PROMOTED`.
- [x] `wt idea state` + TUI mutation `state` work.
- [x] `next_step_for_idea` empty for `SHIPPED`.
- [x] Focused tests pass; `spec_lint` clean.

## Test plan

Executed: `tests/test_close.py`, `test_reconcile.py`, pull_status SHIPPED export test,
`test_tui_mutations.py::test_apply_mutation_state_to_shipped`, `test_completion.py`.

## Definition of done

- [x] AC met; ledger updated; IDEA-290 questions resolved at promote.

## Open questions

_(none)_
