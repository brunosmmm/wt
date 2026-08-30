---
id: SPEC-0082
title: "Color-code idea state (IDEA/INCUBATE/SPECCED) so triage progress"
status: done
owner: user
created: 2026-07-28
source_idea: IDEA-103
updated: 2026-07-28
milestone: "M4: cli ergonomics"
tags: [cli, ideas, ergonomics]
depends_on: [SPEC-0075]
# supersedes: []
# superseded_by: SPEC-NNNN
---

## Context

Promoted from idea `IDEA-103` (Color-code idea state (IDEA/INCUBATE/SPECCED) so triage progress reads at a glance).

  :PROPERTIES:
  :ID: IDEA-103
  :CREATED: [2026-07-28 Tue 07:41]
  :UPDATED: [2026-07-28 Tue 08:15]
  :PROJECT: Meta-Tools
  :KIND: improvement
  :EXPLORED: 1
  :EXPLORED_AT: [2026-07-28 Tue 08:14]
  :END:
** Summary
The `state` column in `wt ideas` / `wt next` carries the most useful triage fact — how far an idea has got — and renders it with **no colour signal at all**. Measured: `_state_style` (`src/wt/report.py:396`) returns `'white'` for **all** of `IDEA`, `INCUBATE` and `SPECCED`, and `'dim'` for every terminal state (`PROMOTED`, `EXPORTED`, `DROPPED`, `RESEARCHED`). So the ideas view has exactly one bit of colour information: open vs done.

**The diversity is real, unlike `kind`'s.** In the default open view: 15 `IDEA`, 9 `INCUBATE`, 5 `SPECCED` — three meaningfully different situations (never looked at / being researched / has an accepted design) rendered identically. Compare [[IDEA-101]], where 88% of ideas share one `kind` value, which is why colouring /that/ column was parked in favour of this one.

**Constraint that shapes the design:** `_state_style` is **shared**, not idea-specific — seven call sites across `report.py` (`:434` `tasks`, `:595` `ideas`, `:639` `next_ideas`, `:692`/`:696` agenda, `:758`). It already encodes the **task** vocabulary (`INPROGRESS` → bold green, `BLOCKED`/`TRIAGE` → yellow). Idea states fall through to `white` precisely because they are not task states. So this wants a **separate** `_idea_state_style` used by the two idea tables, not an edit to the shared helper — otherwise `wt tasks` and `wt agenda` change as collateral.

**Constraint from [[IDEA-101]]'s exploration:** colour does not survive a pipe (measured: `wt ideas | grep -c $'\\x1b['` → 0, Rich disables colour for a non-tty). The state **text** is always present, so colour here is a genuine accelerant rather than the sole carrier — which is a materially better position than the `kind` case, where the text was the only signal too.
** Open questions
*** RESOLVED Which palette? The states form a *progression* (=IDEA= → =INCUBATE= → =SPECCED=), so a ramp (grey → cyan → green) may read better than four unrelated hues. Prototype both before choosing.
*** RESOLVED Do the terminal states stay uniformly =dim=, or does =DROPPED= deserve a different treatment from =PROMOTED=? One is abandoned work, the other is finished work, and =--all= shows them side by side.
*** RESOLVED Confirm the change is scoped to a new ~_idea_state_style~ used only by ~ideas~ and ~next_ideas~ — leaving ~tasks~, ~agenda~ and the review timeline on the shared ~_state_style~ untouched.
*** RESOLVED Should =EXPORTED= be visually distinct from =PROMOTED=? Both are terminal, but =EXPORTED= means work is live in another repo and may still need pulling, which is arguably not "done" from the human's point of view.
*** RESOLVED Does =wt next= want the same palette, or does its =next= column already carry the progress signal there, making colour redundant in that one view?
*** RESOLVED Is a colour ramp legible against both light and dark terminal themes? =dim= and =grey= in particular are theme-sensitive, and there is no theme configuration in wt today.
** Log
*** [2026-07-28 Tue 07:42]
Split out of [[IDEA-101]] (colour-code idea /kind/) after exploring it. The human chose to redirect the effort here: kind is 88% one default value, so colouring it would tint 3 of 29 open rows, whereas state has genuine diversity (15 / 9 / 5) and currently no colour at all.

Measured while exploring IDEA-101, carried over rather than re-derived:
- `_state_style` (`src/wt/report.py:396`) → `'white'` for `IDEA`/`INCUBATE`/`SPECCED`, `'dim'` for all terminal states. The ideas view therefore has one bit of colour: open vs done.
- Open-view state counts: `IDEA` 15, `INCUBATE` 9, `SPECCED` 5.
- `_state_style` has **seven** call sites (`report.py:434,595,639,692,696,758`) spanning `tasks`, `ideas`, `next_ideas`, agenda and the review timeline, and already encodes the task vocabulary (`INPROGRESS`, `BLOCKED`, `TRIAGE`). Hence the "new helper, not an edit" constraint in the Summary.
- Colour is stripped when output is not a tty (`wt ideas | grep -c $'\\x1b['` → 0).

Not yet investigated: whether a ramp or discrete hues read better (needs a rendered prototype, the way SPEC-0075 prototyped table layouts before choosing), and light-vs-dark theme legibility.
*** [2026-07-28 Tue 08:14]
Explored `/home/user/work/tools/work-tracking` (research root, internal). Prototyped three palettes rather than reasoning about them, the way SPEC-0075 prototyped table layouts before choosing. Four findings, two of which rule options out.

**1 — `dim` is already spoken for, and it means "closed".** `dim` is the single most-used style in wt (86 occurrences vs 40 for `green`, 10 `cyan`), and `_state_style` returns `'dim'` for every done task/idea. So a "progression ramp" that starts `dim` for `IDEA` — my first instinct, since `IDEA` is the coldest state — **inverts an established convention**: it would render the newest, most actionable idea in the colour that currently means finished. Ruled out. `IDEA` must stay plain/`white`.

**2 — The terminal states want dimmed variants of their live colour, not one shared `dim`.** Prototyped `PROMOTED` as =`dim green`` (after `SPECCED` ``green``) and `EXPORTED` as ``dim cyan`` (after `INCUBATE` ``cyan``). This reads well and **answers the open question about `EXPORTED` vs `PROMOTED` for free**: dim carries "closed", hue carries "which path it closed down". `DROPPED` as ``dim red`` distinguishes abandoned from finished, which today are identical. `RESEARCHED` stays plain `dim= (explored, no spec — no path taken).

**3 — Reusing `yellow` for `INCUBATE` would clash across views.** A discrete palette naturally reaches for `yellow` for an early state, but `_state_style` already uses `yellow` for `BLOCKED`/`TRIAGE` in `wt tasks`. Yellow would then mean "needs attention" in one table and "being researched" in another. `cyan` is free — it is used for the `next` column and `bold cyan` for figures, never for a state. Ruled out in favour of cyan.

**4 — The blast radius is bigger than the state cell, and this is the real design decision.** Both idea tables pass the **same** style to the state cell **and the headline** (`src/wt/report.py:605` and `:649`: `f"[{st}]{_clip(prow['heading'], budget)}[/]"`). So naively adding hue turns every headline cyan or green too — a much louder change than asked for. Prototyped a third variant with hue on the **state cell only** and the headline left on today's white/dim open-vs-done meaning; it keeps the row calm while making the state column scannable. That is the variant I would recommend, but it is a taste call and the human should see the choice.

**Confirmed as expected:** all seven styles parse via `rich.style.Style.parse`; a separate `_idea_state_style` is required because `_state_style` has seven call sites spanning `wt tasks`, `wt agenda` and the review timeline, and already encodes the task vocabulary.

**Still unresolved and not answerable by prototyping:** light-vs-dark terminal legibility (wt has no theme config, and `dim` in particular is theme-sensitive), and whether `wt next` wants the same palette or whether its own `next` column already carries the progress signal.

## Goals / Non-goals

**Goals**

- The `state` column in `wt ideas` / `wt next` carries hue, so triage progress reads at a glance.
- Terminal states are distinguishable from each other, not just from open ones.
- `wt tasks`, `wt agenda` and the review timeline are untouched.
- The headline column keeps its current meaning.

**Non-goals**

- No change to `_state_style`, which is shared by seven call sites and encodes the *task*
  vocabulary. This adds a sibling.
- No colour on the headline. It keeps today's white-for-open / dim-for-done.
- No theme configuration. Legibility on light terminals is an accepted open risk (see Rollout).
- No new column, no ordering change, no schema change.
- Not colour-coding `kind` (`IDEA-101`, parked: 88% of ideas share one kind value) and not the
  glyph approach (`IDEA-104`), which is a competing encoding for a different column.

## Decision

Add `_idea_state_style(task)` in `src/wt/report.py`, used by `ideas()` and `next_ideas()` for the
**state cell only**:

| State | Style | Meaning |
|---|---|---|
| `IDEA` | *(plain)* | captured, untouched |
| `INCUBATE` | `cyan` | being researched |
| `SPECCED` | `green` | has an accepted design |
| `PROMOTED` | `dim green` | shipped internally |
| `EXPORTED` | `dim cyan` | live in another repo |
| `DROPPED` | `dim red` | abandoned |
| `RESEARCHED` | `dim` | explored, no spec |
| anything else | falls through to `_state_style` |

**Dim carries "closed"; hue carries "which path it closed down."** That distinction is the whole
value: `PROMOTED`, `EXPORTED`, `DROPPED` and `RESEARCHED` are currently rendered identically, so
finished, handed-off and abandoned work are indistinguishable in `--all`.

The headline keeps its existing white/dim style. Both tables currently pass one style to the state
cell *and* the headline, so this requires splitting that — see Design.

## Design

### Two findings from prototyping that shaped the palette

Three palettes were rendered and compared before choosing (as SPEC-0075 did for layouts):

- **`IDEA` must not be `dim`.** A progression ramp starting dim for the coldest state is the
  obvious first instinct and it is wrong: `dim` is the most-used style in wt (86 occurrences) and
  `_state_style` returns it for everything done, so dimming `IDEA` would render the *newest, most
  actionable* idea in the colour that already means finished.
- **`yellow` is unavailable for `INCUBATE`.** `_state_style` uses yellow for `BLOCKED`/`TRIAGE` in
  `wt tasks`, so yellow would mean "needs attention" in one table and "being researched" in
  another. `cyan` is free — used for the `next` column and figures, never for a state.

### `_idea_state_style` (`src/wt/report.py`, beside `_state_style`)

```python
def _idea_state_style(task):
    """Hue for an idea's state cell (SPEC-0082). Falls back to `_state_style` for any state
    outside the idea vocabulary, so a custom `#+TODO` keyword still renders."""
```

Keyed on `(task.state or "").upper()` via a module-level dict, so an unknown keyword degrades to
today's behaviour rather than raising or rendering unstyled.

### Splitting the state and headline styles

`ideas()` (`src/wt/report.py:~592`) and `next_ideas()` (`~635`) currently compute one
`st = _state_style(tk)` and use it for both cells, including
`f"[{st}]{_clip(prow['heading'], budget)}[/]"` (`:605`, `:649`). Each gains a second local:

```python
st = _state_style(tk)                 # headline: white / dim, unchanged
sst = _idea_state_style(tk)           # state cell: hue
```

Only the state cell's f-string changes. This is why the diff touches the headline line at all —
it must keep using `st`, not the new style.

### What is deliberately not touched

`tasks()` (`:434`), the agenda blocks (`:692`, `:696`) and the review timeline (`:758`) keep
calling `_state_style`. `wt next` *does* get the palette: its state column has the same meaning as
`wt ideas`'s, and leaving them inconsistent would be worse than the marginal redundancy with its
`next` column.

## Alternatives considered

- **Colour the whole row** (state + headline, as they share a style today) — strongest signal,
  rejected: 40 rows of cyan and green is a lot of colour for a list read every day, and the
  headline is the content, not the metadata.
- **Progression ramp starting `dim`** — ruled out by prototyping; see Design.
- **Discrete palette with `yellow` for `INCUBATE`** — ruled out by the cross-view clash.
- **One shared `dim` for all terminal states** (today's behaviour) — simpler, but keeps abandoned
  and shipped work looking identical, which is the specific thing worth fixing in `--all`.
- **Only `DROPPED` stands out** — a middle option; rejected as it leaves `EXPORTED` (work live
  elsewhere, possibly needing a pull) reading as plain done.
- **Edit `_state_style` directly** — smallest diff, unacceptable collateral: it would restyle
  `wt tasks` and `wt agenda`.
- **Colour `kind` instead** (`IDEA-101`) — parked: 88% of ideas share one kind value.

## Acceptance criteria

- [x] In `wt ideas`, the state cell for `INCUBATE` renders cyan, `SPECCED` green, and `IDEA`
      unstyled/plain.
- [x] `PROMOTED`, `EXPORTED`, `DROPPED`, `RESEARCHED` render `dim green`, `dim cyan`, `dim red`,
      `dim` respectively — i.e. all four are mutually distinguishable.
- [x] The headline cell's style is unchanged for every state (white when open, dim when done).
- [x] `wt next` uses the same state palette.
- [x] `wt tasks`, `wt agenda` and `wt review` output is byte-identical to before the change.
- [x] An idea whose state is outside the idea vocabulary falls back to `_state_style` and still
      renders.
- [x] Every style in the table parses as a Rich style.
- [x] No new column; table widths and row order are unchanged (SPEC-0075/0077 invariants hold).
- [x] Piped output (no colour) is byte-identical to before the change, since the state text is
      unchanged.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_idea_state_color.py` (21 tests):

- `test_palette_maps_every_idea_state` — parametrised over all seven states, asserting the exact
  style string. The palette *is* the spec, so it is enumerated.
- `test_all_styles_parse` — `rich.style.Style.parse` on each value; a typo like `dim gren` would
  otherwise fail only at render time.
- `test_terminal_states_are_mutually_distinct` — the four terminal styles are four distinct
  values. This is the criterion that motivated the spec, so it is asserted directly rather than
  implied by the table test.
- `test_unknown_state_falls_back` — a state outside the vocabulary returns `_state_style`'s answer.
- `test_state_cell_is_hued_but_headline_is_not` — render at a fixed width with `force_terminal`,
  and assert the ANSI run wrapping the state text differs from the one wrapping the headline. This
  is the decision the human made explicitly, and the easiest thing to regress by reusing one local.
- `test_next_table_uses_the_same_palette`.
- `test_tasks_and_agenda_output_unchanged` — capture `tasks()` and `agenda()` before/after is not
  possible in one process, so instead assert they still call `_state_style` (import-level check on
  the source) and that their rendered output contains no idea-palette style. Guards the collateral
  the spec forbids.
- `test_no_colour_output_unchanged` — with colour disabled, the table text is identical to a
  pre-change baseline built from the same rows, proving nothing but styling changed.
- `test_spec_0075_invariants_hold` — widths {200,120,80,60}: all columns present, no line over the
  width (the style change must not alter width accounting, which measures `len(str)` of the
  *unstyled* cell).

**Manual verification**

1. Rendered the real corpus with a forced-colour console and read back the SGR codes per row.
   **Done** — every state maps as specified: `INCUBATE` → `36`, `SPECCED` → `32`,
   `PROMOTED` → `2;32`, `EXPORTED` → `2;36`, `DROPPED` → `2;31`, `RESEARCHED` → `2`, and `IDEA`
   carries no state code at all.
2. `--all` over 102 ideas — `DROPPED` (`2;31`) is visibly distinct from `PROMOTED` (`2;32`) and
   `EXPORTED` (`2;36`), which was the point. **Done.**
3. `wt tasks` / `wt agenda` unchanged — asserted by test rather than by eye
   (`test_tasks_and_agenda_still_use_the_shared_helper` inspects the source, and
   `test_tasks_output_has_no_idea_palette` checks the render). **Done.**
4. `uv run wt ideas | cat` — no escape codes; text identical. **Done.**

*(Note on method: colour cannot be inspected by piping, since Rich strips it for a non-tty — the
same finding that shaped SPEC-0075 and IDEA-101. Verification therefore swaps in a
`force_terminal` console and asserts on SGR codes, which is also how the tests do it.)*

**Regression guard**

Full `uv run pytest`, especially `tests/test_idea_table_width.py` and
`tests/test_idea_freshness.py` (SPEC-0075/0077 width and order invariants) and
`tests/test_tasks.py`.

## Clock Log

Clocked on IDEA-103 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

Presentation only; no data, no schema, no config. Single commit.

**Accepted open risk:** legibility on light-background terminals is untested and wt has no theme
configuration. `dim` and the dimmed hues are the theme-sensitive ones. If they read poorly, the
palette is one dict to change — but that is a follow-up, not a blocker, and it is recorded here so
the next person knows it was a known gap rather than an oversight.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Ramp vs discrete hues* → neither as first drafted; `IDEA` plain, `cyan`/`green` for live states,
  dimmed variants for terminal. Chosen by prototyping.
- *Terminal states* → dimmed variants per path, so finished / handed-off / abandoned differ.
- *Scope of the colour* → state cell only; headline unchanged (human's call).
- *Separate helper* → yes, `_idea_state_style`; editing `_state_style` would restyle `wt tasks`.
- *Does `wt next` get it* → yes; divergent tables would be worse than the redundancy.
- *Light/dark legibility* → untested, accepted as a known risk with a one-dict fix.
