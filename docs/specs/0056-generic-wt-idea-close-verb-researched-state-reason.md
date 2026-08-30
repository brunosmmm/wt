---
id: SPEC-0056
title: "Generic wt idea close verb + RESEARCHED state + reason"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
parent: SPEC-0055
source_idea: IDEA-066
milestone: "M4: cli ergonomics"
tags: [ideas, workflow, lifecycle]
---

## Context

Foundation child of [SPEC-0055](./0055-complete-the-idea-terminal-outcome-model-first.md).
Today an idea can only be terminated as `DROPPED` via the generic, reasonless
`wt state IDEA-NNN DROPPED`, and there is no state for "explored, no spec needed" (the
`IDEA-062` case). This spec adds a first-class `wt idea close` verb, a new `RESEARCHED`
terminal state, and reason capture. See the epic for the cross-cutting design and why
`set_state` gives listing/`CLOSED:`/reversibility for free while property writing is new.

## Decision

Add `wt idea close SELECTOR --as [drop|researched] [--reason TEXT]`:
- `--as drop` → `DROPPED`; `--as researched` → new `RESEARCHED` terminal keyword — both via
  `set_state` (so the `CLOSED:` stamp and reversibility are unchanged).
- `--reason` is recorded as a `CLOSE_REASON` property **and** a dated Log line.

Reason/pointer writing reuses the existing `org_write.set_property` (SPEC-0013); the one new
primitive this spec adds is `ensure_idea_keyword` (to make `RESEARCHED` settable in the file).

## Design

- **`config.py`:** append `RESEARCHED` to `org_idea_keywords` (done side:
  `… | PROMOTED EXPORTED DROPPED RESEARCHED`) so `is_idea` still recognizes a `RESEARCHED`
  idea and the env fallback knows the keyword.
- **File keyword header (`org_write.py`, `ensure_idea_keyword`):** since a file's own `#+TODO`
  wins, extend the ideas file's idea-state `#+TODO` line (the one containing `INCUBATE`) to
  include `RESEARCHED` in its done section if absent. Idempotent; drift-safe (only appends a
  token). Called by `close_idea` before `set_state`.
- **Property writer:** reuse the **existing** `org_write.set_property` (SPEC-0013) — it already
  add/updates a `:KEY: value` in the idea's drawer, drift-guarded + atomic. (The epic assumed a
  new writer; the exploration missed that `set_property` already existed. The one genuinely new
  primitive is `ensure_idea_keyword`.)
- **`close_idea(cfg, selector, outcome, reason=None)` (`explore.py`):** validate `outcome`
  in `{drop, researched}`; map to `DROPPED`/`RESEARCHED`; `ensure_idea_keyword` → `set_state`
  → (`set_property(task, "CLOSE_REASON", reason)` and `append_log("Closed as {outcome}. …")`).
  Re-resolve between writes (line shifts). Pointers are resolved before any write, so a bad
  target fails clean.
- **CLI (`cli.py`):** `idea close` command with `--as` (required `Choice`), `--reason`.
- **`workflow.py`:** `next_step_for_idea` returns `""` for `RESEARCHED` (mirrors `DROPPED`).
- **`report.py`:** `collect_next_tasks` also omits `RESEARCHED` (parity with the `DROPPED`
  filter); default `wt ideas` already hides it via `is_done`.

## Alternatives considered

- **Separate `wt idea drop` / `wt idea archive` verbs** — rejected per owner: one generic
  `close --as` covers all outcomes and is the extension point for SPEC-0057's pointers.
- **Reason as Log-only (no property)** — rejected: a property is queryable/greppable; the Log
  line adds chronology. Keep both.

## Acceptance criteria

- [x] `wt idea close IDEA-NNN --as drop --reason "x"` sets `DROPPED` + `CLOSED:` stamp +
      `:CLOSE_REASON: x` property + a Log line, in one command.
- [x] `wt idea close IDEA-NNN --as researched --reason "y"` sets the new `RESEARCHED` state
      (valid in the file's `#+TODO`) with reason property + Log line.
- [x] `wt idea close --as bogus` and closing a non-idea error cleanly (no write).
- [x] `RESEARCHED` ideas are hidden from default `wt ideas`/`wt next` (no hint), shown under
      `--all` and in `wt idea show`; reopen via `wt state IDEA-NNN INCUBATE` drops `CLOSED:`.
- [x] `set_property` adds a new key and updates an existing one without disturbing
      other drawer lines.

## Test plan

- **Automated tests** (`tests/test_close.py`): close as drop/researched sets keyword + CLOSED +
  `CLOSE_REASON` + Log; `ensure_idea_keyword` idempotent and makes `RESEARCHED` settable;
  `set_property` add/update; `--as bogus`/non-idea raise with no write; `RESEARCHED`
  absent from `wt next`/default `wt ideas`, present under `--all`; reopen path.
- **Manual verification:** `wt idea close IDEA-062 --as researched --reason "folded into 059"`;
  confirm it leaves `wt next` and shows with its reason.
- **Regression guard:** full `uv run pytest` green; `wt state`, `PROMOTED`/`EXPORTED`, and
  existing idea listings unchanged.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green; manual step performed.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.
