---
id: SPEC-0102
title: "Explore mutations in the TUI desk"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
parent: SPEC-0098
depends_on: [SPEC-0099, SPEC-0100, SPEC-0101]
milestone: "M5: interactive desk"
source_idea: IDEA-132
tags: [tui, explore]
---

## Context

Child of [SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) (IDEA-132). Wire the
read-only desk to library mutators for day-to-day explore work.

## Goals / Non-goals

**Goals**
- From the desk: capture new idea; append log; edit summary; add / resolve / unresolve /
  edit / delete questions; mark-explored; retitle.
- After every write: re-`resolve_selector` + reload enrichment; friendly drift messaging.
- Questions addressed by 1-based index (SPEC-0101).

**Non-goals**
- Promote / generate / export wizards.
- Inventing write rules outside `explore` / `org_write`.
- Metadata/clock UI (SPEC-0103) beyond what's needed to call existing APIs if already shown.

## Decision

Bind Textual inputs/modals to existing library functions (including SPEC-0101 APIs). No
subprocess to `wt`. Failures (drift, validation) show in-UI and trigger refresh.

## Design

**As shipped.**

*One dispatch table.* `model.apply_mutation(cfg, action, selector, **kw)` maps an action name
to its library mutator (`log`, `summary`, `retitle`, `explored`, `question_add|resolve|
unresolve|edit|delete`), plus `model.capture_idea`. The widget layer *names* an action and
hands over; it owns no write rules, and an unknown action raises rather than silently no-opping
in a key handler. Both live in `model.py`, so every mutation is testable without Textual.

*Bindings on the desk.* `l` log · `s` summary · `?` questions · `c` capture · `t` retitle ·
`x` mark-explored (the last two `show=False` to keep the footer scannable).

*Modals.* `TextPrompt` (one-line, Enter submits, Esc cancels) and `BodyPrompt` (TextArea for
Summary — **ctrl+s saves**, because Enter has to stay a newline). Both dismiss `None` on cancel,
which the callers treat as "no write".

*Questions get their own screen* rather than inline keys on the detail pane: resolve /
unresolve / edit / delete each need a *selected question*, and a second cursor on the main desk
would cost more chrome than it saves. `enter` toggles resolve/reopen, `a` add, `e` edit,
`d` delete, `esc` close. It dismisses `True` when anything was written so the desk reloads.

- **`enter` is deliberately not a `Binding`** on that screen: the focused `DataTable` consumes
  it for its own select action, so a screen binding never fires. Handling `DataTable.RowSelected`
  is what that keypress actually produces. (Found by a failing pilot test, not by reading docs.)
- Acting with nothing selected is a no-op, not a crash — `index` returns `None` when the table
  is empty, so `d`/`e`/`enter` after deleting the last question are safe.

*Post-write refresh.* `IdeaDesk.mutate` always calls `reload(keep_id=…)` — on success *and* on
failure. A `ValueError` (the writers' drift guard) surfaces via `notify(severity="error")` and
still reloads from disk, which is exactly the recovery a drifted file needs; the session stays
alive. The questions screen does the same into its own status line.

*CSS is built by `.replace()`, not `%`-formatting.* CSS is full of literal `%` — and so are
comments about it — which `%`-formatting reads as conversion specs. That broke the module twice
during this spec; substitution is immune.

*Supersedes half of SPEC-0100's read-only guard.* That test asserted the app module named no
mutator at all. What remains is the permanent epic invariant: the desk must never `subprocess`
out to `wt` and never touch org files directly — now asserted over **both** `app.py` and
`model.py`.

## Alternatives considered

- **Ship add/resolve-only without SPEC-0101** — rejected (epic Q4).
- **Shell out to CLI** — rejected; dual paths.

## Acceptance criteria

- [x] Each listed mutation works from the desk and persists to org (verified via
      `wt idea show`).
- [x] Post-write refresh always runs; drift is non-fatal to the app session.
- [x] No promote/export UI.
- [x] Classic CLI mutators still work identically.

## Test plan

**Executed 2026-07-30.** `tests/test_tui_mutations.py` — 13 tests (4 need no Textual).

- **Dispatch (base install):** one test walks all nine actions end-to-end and asserts the
  resulting summary / log / heading / questions / explored count; unknown action raises;
  `capture_idea` returns the new id and refuses empty text; a mutation written by the desk is
  then read back through `wt idea show` (the "classic CLI agrees" AC).
- **Pilot (bindings):** `l` writes a log note · `c` captures **and selects the new idea** ·
  `x` increments explored · `s` saves via ctrl+s · `esc` on a prompt leaves the file
  byte-identical.
- **Pilot (questions screen):** full CRUD in one drive — resolve → reopen → move → edit →
  add → delete, asserting the org state after each; plus a screen that has had its last
  question deleted still absorbs `d`/`e`/`enter` without raising.
- **Drift:** `apply_mutation` monkeypatched to raise `ValueError` — app stays running and the
  list reloads rather than emptying.
- **Read-only guard (rewritten):** `subprocess` / `os.system` / `popen` /
  `_atomic_backup_write` / direct file reads appear in neither `app.py` nor `model.py`.
- **Manual verification:** drove a real `IdeaDesk` against an isolated `WT_CONFIG_DIR` org —
  log → summary → 2 questions → resolve #2 → mark-explored → capture — then read the file:
  `** Summary / summary via desk`, `*** OPEN an open one`, `*** RESOLVED to resolve`,
  `:EXPLORED: 1` + `:EXPLORED_AT:`, a second `* IDEA captured in desk`, and the idea correctly
  advanced `IDEA → INCUBATE`.
- **Regression guard:** `uv run pytest` — 853 passed; SPEC-0101 and CLI question suites green.

## Clock Log

`wt idea clock-in/out` on IDEA-132 (org LOGBOOK, not mirrored here).

## Rollout / migration

After SPEC-0099, 0100, and 0101.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
