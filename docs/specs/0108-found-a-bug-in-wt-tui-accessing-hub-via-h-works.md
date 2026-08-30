---
id: SPEC-0108
title: "Hub tab must load on any activation route, not only the h binding"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
depends_on: [SPEC-0104]
milestone: "M5: interactive desk"
source_idea: IDEA-138
tags: [tui, hub, bug]
---

## Context

From `IDEA-138`, reported from real use. Clicking the **hub** tab shows a blank pane; pressing
`h` works.

**Reproduced 2026-07-30.** Fresh desk, activate the hub tab the way a mouse does
(`TabbedContent.active = "tab-hub"`, never pressing `h`) → `hub_rows=0, cols=0` and an empty
grid. Via `h` → `hub_rows=77, cols=4`.

**Root cause.** Loading is bound to the **keybinding handler**, not to the tab becoming active.
`action_toggle_hub` flips `TabbedContent.active` *and* calls `load_hub()`; the `#hub` DataTable
gets its rows — and even its **columns** — only there. Every other route into the tab (mouse
click, Textual's own tab navigation) arrives at a pane that was never loaded.

**Why it shipped green.** Every test in `tests/test_tui_hub.py` drives `pilot.press("h")`. A
test suite that reaches a surface only the way its authxx intended cannot find a bug in the
other routes. Same lesson as SPEC-0105, where the search tests asserted state rather than what
was on screen.

**Class, not instance.** This repeats the `enter` mistake from SPEC-0102: behaviour attached to
*one input path* rather than to the *state change* it is actually about.

## Goals / Non-goals

**Goals**
- The hub loads whenever its tab becomes active, by any route.
- `h` keeps working, including toggling back to ideas.
- Focus behaves the same on every route.
- A regression test that reaches the tab **without** the keybinding.

**Non-goals**
- Changing what the hub shows, or `hub_payload` (SPEC-0104 stands).
- Making the hub writable.
- Auditing every other binding for the same class of bug (worth doing; not this spec).

## Decision

React to the **tab activation event** rather than to the key. `h` becomes a plain tab switch;
loading and focus hang off `TabbedContent.TabActivated`, so click, keyboard navigation and the
binding all converge on one path.

## Design

- Handle `TabbedContent.TabActivated` (or the equivalent Textual 8 event) on the desk. When the
  activated pane is `tab-hub`, call `load_hub()` and focus `#hub`; when it is `tab-ideas`, focus
  `#list`.
- `action_toggle_hub` reduces to flipping `TabbedContent.active` — no loading, no focus. It
  cannot drift from the click path because it no longer has its own path.
- Columns are added inside `load_hub` already (guarded by `if not table.columns`), so a first
  activation from any route both creates columns and fills rows.
- **Reload on every activation**, not once (Q1 on the idea): the hub is a triage view over
  ideas, specs and outbox that the desk itself mutates, so a stale hub is worse than a cheap
  reload. `load_hub` performs no writes.

## Alternatives considered

- **Populate the hub eagerly at mount** — rejected: pays `hub_payload` (which walks the specs
  dir and outbox) on every desk launch, including sessions that never open the tab.
- **Also call `load_hub` from a click handler** — rejected: that is two paths again, which is
  the bug.
- **Remove the `h` binding, click only** — rejected: keyboard-first is the point of the desk.

## Acceptance criteria

- [x] Activating the hub tab **without** pressing `h` renders the populated hub.
- [x] `h` still opens the hub and toggles back to ideas.
- [x] Focus lands on `#hub` on entry and `#list` on return, by any route.
- [x] The hub reflects changes made since the desk launched.
- [x] No writes from browsing (SPEC-0104's guarantee holds).

## Test plan

**Executed 2026-07-30.** `tests/test_tui_hub.py` grew to 15 tests (4 new).

- **The reported symptom, clicked:** a **real `pilot.click`** on the hub `ContentTab` header of
  a fresh app — not `active = …` — asserting rows > 0, four columns, and focus on `#hub`. The
  report was "clicking the hub tab", so the test clicks.
- **Both routes agree:** `h` and direct activation produce the same non-zero row count.
- **Focus on return** by the non-key route.
- **Staleness:** capture an idea while on the ideas tab, re-activate the hub, expect one more
  row — pinning the reload-every-activation decision.

**Verified against the pre-fix build**: the old `action_toggle_hub` restored, **3 of the 4 new
tests fail** (click-loads, routes-agree, focus-on-return); fix restored, all 15 pass. The
staleness test passes on both builds — it guards the reload decision, not this bug, and is not
claimed as a regression guard for it.

- **Manual verification:** a real click against the live org — `active=tab-hub rows=79 cols=4
  focus=True`, where the same click previously produced `rows=0 cols=0`.
- **Regression guard:** `uv run pytest` — 918 passed; SPEC-0104's no-write guard still holds.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — both resolved on IDEA-138: reload every activation; focus follows the tab on all routes)

## Follow-up worth its own idea

Audit the desk for other behaviour bound to a single input path rather than to a state change.
`enter` (SPEC-0102) and this are two instances of one pattern.
