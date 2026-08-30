---
id: SPEC-0105
title: "Desk search bar is invisible and does not filter as you type"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
depends_on: [SPEC-0100]
milestone: "M5: interactive desk"
source_idea: IDEA-135
tags: [tui, ideas, search]
---

## Context

Promoted from `IDEA-135`, reported from real use of the desk shipped by
[SPEC-0100](./0100-read-only-ideas-list-and-detail-desk.md). Deliberately **not** a child of the
[SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) epic: that epic's acceptance criteria
were genuinely met and it is `done`. Re-parenting a later defect into it would reopen a closed
epic and make the ledger's timeline less faithful, not more.

**Bug.** The `/` search box never renders. `#tabs` at `1fr` consumed every flow row, so the
`Input` — **3 rows tall by default, because it has a border** — was laid out at y=19 on a
20-row screen, with `#hint` and the docked `Footer` on the same line and the Footer painted
over it. It collected keystrokes correctly the whole time.

**Why the tests missed it.** SPEC-0100's pilot asserted `app.query == "entirely"` and that the
rows filtered — the resulting *state*. Nothing asserted the box is on screen. A test can
confirm a feature works and still not confirm anyone can use it.

**Missing behaviour.** Search applies only on Enter; a triage desk should filter as you type.

**Constraint.** `search_idea_tasks` re-reads every idea's enrichment — measured **~300ms** over
the live 43-idea corpus (a one-character query returns 131 hits, since search scans
open+closed). Running that per keystroke would block the UI at typing speed.

## Goals / Non-goals

**Goals**
- The search box is visible, shows what is typed, and is distinguishable from the footer.
- Typing filters the list without pressing Enter.
- One search definition: live filtering calls the same `search_idea_tasks` the CLI uses.
- A regression test that asserts the box is *rendered*, not merely stateful.

**Non-goals**
- A new in-memory search index or caching layer.
- Changing ranking, tokenisation, or which corpus `--query` scans (SPEC-0086 stands).
- Live search in the hub tab.

## Decision

Give the bottom strip explicit heights so search / hint / footer each own a row, and make the
search `Input` a borderless single row. Filter as you type via a **debounced** timer rather
than a per-keystroke call: at ~300ms per search, a synchronous call on every keystroke would
stall the UI, and a cache would fork the search definition.

## Design

**Layout fix.** `#tabs { height: 1fr }` plus explicit `height: 1` on `#search` and `#hint`, and
`border: none; padding: 0 1; background: $panel` on the input so it reads as a bar rather than
a stray line of text. Verified by widget regions: tabs y=1..16, search y=17, hint y=18, footer
y=19 — four distinct rows on a 20-row screen.

**Debounced live filter.** `Input.Changed` restarts a `set_timer(SEARCH_DEBOUNCE)`; the timer
runs the existing `reload()`. Consecutive keystrokes cancel the pending timer, so a burst of
typing costs one search. `SEARCH_DEBOUNCE = 0.3s` — roughly one search duration, so the desk
never queues work faster than it can finish it.

- Enter still applies immediately and closes the box (unchanged muscle memory).
- Esc still cancels and restores the unfiltered list.
- Clearing the box live restores the unfiltered list, so backspacing out of a search does not
  strand the user on an empty result.

## Alternatives considered

- **Search on every keystroke, synchronously** — rejected; ~300ms per call is a visible stall.
- **Cache the enrichment corpus for the session** — rejected here; it forks the definition of
  "search" away from `search_idea_tasks` and adds a staleness question the desk does not
  otherwise have. Worth revisiting only if the corpus grows enough that debounce stops hiding it.
- **A modal search prompt** (like log / summary / capture) — rejected; a modal covers the list
  it is filtering, which is exactly what live filtering exists to show.

## Acceptance criteria

- [x] The search box renders on its own row and displays typed text.
- [x] Typing filters the list with no Enter press.
- [x] Enter and Esc keep their existing behaviour.
- [x] Clearing the query live restores the unfiltered list.
- [x] Filtering still goes through `search_idea_tasks` (no second search path).

## Test plan

**Executed 2026-07-30.** `tests/test_tui_search.py` — 9 tests.

- **Visibility:** typed text appears **on the search box's own row** (located via
  `region.y`), and search / hint / footer occupy three distinct rows all within the screen.
- **Live filter:** typing narrows 3 ideas → 1 with no Enter; clearing restores 3; a 7-character
  burst produces **exactly one** `load_rows` call with a query (debounce, not per keystroke).
- **Existing behaviour:** Enter applies and closes the box; Esc cancels and restores; a
  debounce pending when Esc is pressed does **not** fire afterwards.
- **One definition:** `search_idea_tasks` is called from the model, and no ranking symbol
  (`score_idea_match` / `tokenize_idea_query` / `idea_match_snippet`) appears in the UI.

**Both visibility guards were verified against the broken build** — CSS reverted, tests re-run,
both fail; fix restored, both pass. That check mattered: the *first* cut of the render
assertion passed on the broken build, because it typed `"buffalo"` and looked for it anywhere
on screen, and the seeded idea *"buffalo pipeline rewrite"* already put that word in the list.
It now types a string matching no idea and asserts against the box's own row.

Two harness bugs surfaced and were fixed in `_grid` while proving this:
1. Entities were decoded from a hand-rolled table, so `&#x27;` reached assertions verbatim —
   now `html.unescape`.
2. Rich's SVG draws a fake window title-bar, so `grid[i]` was one row off from screen row `i`.
   Dropped, which is what lets a test use `region.y` directly.

- **Manual verification:** rendered against the live 44-idea org at 100×20 — box visible on its
  own row showing `textual`, list narrowing 44 → 3 without Enter, back to 44 on clear.
- **Regression guard:** `uv run pytest` — 886 passed; the SPEC-0100/0102/0103/0104 desk suites
  (63 TUI tests) green.

## Clock Log

`wt idea clock-in/out` on IDEA-135.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
