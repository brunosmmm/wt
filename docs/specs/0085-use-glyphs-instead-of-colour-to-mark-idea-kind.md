---
id: SPEC-0085
title: "Use glyphs instead of colour to mark idea kind, with a flag to fall"
status: done
owner: user
created: 2026-07-28
source_idea: IDEA-104
updated: 2026-07-28
milestone: "M4: cli ergonomics"
tags: [cli, ideas, ergonomics]
depends_on: [SPEC-0075]
# supersedes: []
# superseded_by: SPEC-NNNN
---

## Context

Promoted from idea `IDEA-104` (Use glyphs instead of colour to mark idea kind, with a flag to fall back to plain text).

  :PROPERTIES:
  :ID: IDEA-104
  :CREATED: [2026-07-28 Tue 07:45]
  :UPDATED: [2026-07-28 Tue 09:04]
  :PROJECT: Meta-Tools
  :KIND: improvement
  :EXPLORED: 1
  :EXPLORED_AT: [2026-07-28 Tue 09:04]
  :END:
  :LOGBOOK:
  CLOCK: [2026-07-28 Tue 09:03]
  :END:
** Summary
**Competing alternative to [[IDEA-101]]**: mark idea `kind` with a glyph (emoji or symbol) rather than a colour, plus a CLI option that forces plain text instead.

**Why it is a genuinely better bet than colour.** [[IDEA-101]]'s exploration measured that colour is **stripped whenever output is not a tty** (`wt ideas | grep -c $'\\x1b['` → 0; Rich disables colour for non-tty). A glyph is **content**, not styling — it survives a pipe, a redirect, `less` without `-R`, a copy-paste into a ticket, and a colour-blind reader. So it addresses the one hard constraint that made colour a weak lever.

**The width argument is also in its favour.** SPEC-0075 went to real trouble reclaiming table width for the headline, and the `kind` column currently reserves up to 12 characters to spell `improvement`. A glyph could replace the word entirely — 1-2 cells instead of 12 — /giving/ width back rather than spending it. That inverts the usual "new signal costs columns" trade.

**The opt-out is part of the ask, not an afterthought.** Emoji are the risky part: inconsistent width (many are double-width, some render as 1 cell in one terminal and 2 in another), font-dependent, and they break the column arithmetic SPEC-0075 built (`_meta_widths` / `_idea_table_widths` measure `len(str)`, which is **not** display width for wide characters). So a `--no-glyphs` / `--plain` escape hatch is required, and the width accounting needs a real fix, not a guess.

**Unresolved premise carried from [[IDEA-101]]:** `kind` is 88% the default value `idea` (90 of 102; 26 of 29 in the open view). A glyph for a field that is almost always the same value has the same thin payoff as a colour for it. This idea inherits that problem — it improves the /mechanism/, not the /signal/. Worth deciding whether it should target `state` instead (as [[IDEA-103]] did for colour), where the diversity actually is.
** Open questions
*** OPEN Real emoji (=🐛 ✨ 🧹=) or ASCII/box symbols (=! + ~ ·=)? Emoji read faster but are double-width in many terminals and font-dependent; symbols are safe but weaker signal.
*** RESOLVED How is display width computed? ~_meta_widths~ (=src/wt/report.py=) measures =len(str)=, which is wrong for wide characters — a double-width glyph would silently overflow the table SPEC-0075 just made exact. Does this need ~wcwidth~ / Rich's own cell-width measurement?
*** RESOLVED What is the opt-out called and what is its scope — =--plain=, =--no-glyphs=, a config key, or honouring =NO_COLOR=/=TERM=dumb=? A config key beats a flag if the preference is permanent.
*** RESOLVED Should the glyph *replace* the kind word (reclaiming ~12 columns for the headline) or *precede* it (redundant but unambiguous)? The former is the real win, the latter is safer.
*** RESOLVED Does this supersede [[IDEA-101]] outright, or are colour and glyph complementary — glyph for pipe-safety, colour as an interactive accelerant on top?
*** OPEN Same open premise as [[IDEA-101]]: with =kind= 88% one default value, is this worth doing for =kind= at all, or should the glyph mechanism target =state= (cf. [[IDEA-103]])?
*** RESOLVED Do glyphs belong in =wt tasks= / =wt agenda= too, or ideas-only? Consistency across views argues one way, scope creep the other.
** Log
*** [2026-07-28 Tue 07:45]
Seeded from conversation while [[IDEA-103]] (colour-code idea /state/) was in flight, explicitly as a **competitor** to [[IDEA-101]] (colour-code idea /kind/).

Carried over from IDEA-101 exploration rather than re-measured:
- Colour is stripped for non-tty output (`wt ideas | grep -c $\x1b[` → 0) — the finding that makes a glyph strictly more robust than a colour.
- `kind` is 88% the default value (`idea` 90 of 102; 26 of 29 open), so the **signal** problem is inherited unchanged; only the **encoding** improves.
- The `kind` column reserves up to 12 characters for `improvement`, against SPEC-0075 having just fought for headline width.

Noted risk not yet investigated: `_meta_widths` / `_idea_table_widths` (SPEC-0075) compute column widths from `len(str)`. That is character count, not terminal cell width, so any double-width glyph would break the exact-width guarantees those helpers now enforce (no line exceeding the console width, no column collapsing). This needs measuring before a palette of emoji is chosen.

No code written. Parked for exploration alongside IDEA-101 / IDEA-103.
*** [2026-07-28 Tue 08:51]
Chosen over [[IDEA-101]] (colour-code kind) on the humans instruction to pick one. Recorded so the reasoning is not lost:

**1 — A glyph is content; colour is styling.** SPEC-0083/0084 were built and then **reverted** because colour proved invisible where it mattered: Rich strips it for a non-tty, and on a dark terminal the light-palette substitution produced no perceptible change at all. A glyph survives a pipe, a redirect, a file, `less` without `-R`, a paste into a ticket, and a colour-blind reader. Choosing the encoding that cannot evaporate is the direct lesson from that revert.

**2 — It pays width back rather than costing it.** The `kind` column reserves up to 12 characters to spell `improvement`; a glyph replaces the word in 1-2 cells and hands ~10 columns to the headline, which is exactly what SPEC-0075 fought to reclaim. Colour returns nothing.

**3 — [[IDEA-101]]'s own exploration argued against it**, and it had already been parked once in favour of [[IDEA-103]] (state colour), which shipped as SPEC-0082.

**Correction to the risk this idea was seeded with.** I flagged that double-width glyphs would break SPEC-0075's exact width accounting. Measured: Rich computes display width itself — `rich.cells.cell_len("🐛")` is 2 while `len` is 1 — and a table containing emoji still renders inside its console width. So the table does not break. What **is** wrong is that `_meta_widths` (`src/wt/report.py`) budgets with `len(str)`, so it would under-reserve one cell per emoji column and Rich would silently take it back from the headline. The fix is one line: measure with `cell_len` instead of `len`. That removes most of the cost this idea was assumed to carry.

**Premise still unresolved, and it caps the value of whichever encoding wins:** `kind` is 88% the default value `idea` (90 of 102; 26 of 29 open) because `wt idea capture` never asks. This idea improves the /encoding/ of a field that carries almost no /signal/. IDEA-101's surviving open question — make kinds actually get set at capture time — is the prerequisite, and is not superseded by this choice.
*** [2026-07-28 Tue 09:04]
Explored `/home/user/work/tools/work-tracking` (research root, internal). Five findings; two shrink the idea, one shrinks the payoff, one is a portability trap.

**1 — The width saving is 7 columns, not the `10 I claimed at seed time.** `_meta_widths~ computes `max(min_width, len(header), widest_capped_cell)`, so the column can never be narrower than its **header**. `kind`'s header is 4 characters, so a 1-2 cell glyph gives `max(4, 4, 2) ` 4`, against today's `max(4, 4, 11) ` 11` for `improvement`. Saving = **7 columns**, handed to the headline. Getting the full 10 would need a 1-character header, which is cryptic. Still the largest single width win available in that table, but it should be stated honestly.

**2 — The width hazard I seeded this with is inert in practice.** I flagged that double-width glyphs would break SPEC-0075's exact accounting. Measured: Rich computes display width itself (`rich.cells.cell_len("🐛")` ` 2 where `len` ` 1) and a table containing emoji renders inside its console width. And because the 4-character header dominates, the reserved 4 cells comfortably exceed a 2-cell glyph, so nothing overflows even with the `len`-based budget. The `cell_len` fix (`report.py:551,554`) is still **correct in principle** and one line, and it becomes load-bearing the moment anyone shortens the header — so it belongs in the change, but as hygiene, not as the blocker I implied.

**3 — Variation selectors are a real trap.** `⚠` is `len 1 / cell_len 1`; `⚠️` — the same glyph with U+FE0F — is `len 2 / cell_len 2`. So two visually identical characters occupy different widths and different string lengths. Any glyph set must be pinned without VS16, or the column silently changes width depending on which codepoint got pasted in.

**4 — Discoverability has to be solved, not assumed.** Replacing the word `improvement` with a symbol means the table no longer says what the symbol means. The footer hint line in `ideas()` (`full text: wt idea show <id> · …`) is the natural home for a compact legend, and it already exists, so this costs no vertical space.

**5 — The premise cap is unchanged and worth restating.** `kind` is 88% the default `idea` (90 of 102; 26 of 29 open, with **zero** open bugs or chores). So in the view you look at daily, a glyph column would show the same glyph 26 times. The 7 reclaimed columns are real and unconditional; the **signal** is not, and does not become real until kinds are actually set at capture time — the question inherited from the superseded [[IDEA-101]].

**Decided while exploring** (not needing the human): the glyph **replaces** the word rather than preceding it, since preceding it saves nothing and the whole width case rests on replacement; the opt-out is a CLI flag rather than config or an env var, per the ask and because the SPEC-0083 revert showed an invisible toggle is worthless; and the legend goes on the existing footer line.

**Left for the human:** emoji versus single-cell geometric symbols. Emoji are instantly readable but carry the double-width, font-fallback and variation-selector risks above, and wt output is frequently piped and pasted. Symbols (`● ◆ ▲ ·`) are all `cell_len 1`, VS16-free, and render in any font that already has the box-drawing characters wt uses — but they need the legend to mean anything.

## Goals / Non-goals

**Goals**

- The `kind` column shows a glyph instead of the word, returning ~7 columns to the headline.
- The signal survives the medium: piped, redirected, pasted, over ssh, and for a colour-blind
  reader — unlike colour, which SPEC-0083/0084 proved evaporates.
- A CLI flag falls back to the plain words.
- Column-width accounting measures *display* width, so a 2-cell glyph cannot be mis-budgeted.

**Non-goals**

- No colour for `kind`. That was `IDEA-101`, now `DROPPED` and superseded by this idea's source.
- Not changing what `kind` *means*, or making capture ask for it. `kind` is 88% the default value,
  which caps the value of any encoding — tracked as `IDEA-101`'s surviving question, not fixed here.
- No glyphs in `wt tasks` / `wt agenda`; tasks carry no `:KIND:`.
- No change to `--json`, which already carries the `kind` text.
- Not shortening the `kind` header to reclaim the last 3 columns.

## Decision

Render `kind` as an emoji, keeping the header `kind`:

| kind | glyph | codepoint |
|---|---|---|
| `idea` | 💡 | U+1F4A1 |
| `bug` | 🐛 | U+1F41B |
| `improvement` | ✨ | U+2728 |
| `chore` | 🧹 | U+1F9F9 |

`wt ideas --plain` (and `wt next --plain`) renders the words instead. A compact legend joins the
existing footer line of `wt ideas`, so the vocabulary is discoverable without costing a row.

`_meta_widths` switches from `len()` to `rich.cells.cell_len()`.

**Why glyphs rather than colour.** A glyph is *content*; colour is *styling*. SPEC-0083 and
SPEC-0084 were built and then reverted precisely because styling disappeared where it mattered —
Rich strips colour for a non-tty, and the light palette produced no perceptible change on a dark
terminal. Choosing an encoding that cannot evaporate is the direct lesson from that revert.

**Why this is width-positive.** `_meta_widths` gives a column
`max(min_width, len(header), widest_capped_cell)`, so `kind` is `max(4, 4, 11) = 11` today for
`improvement`. A glyph makes it `max(4, 4, 2) = 4`. Seven columns move to the headline — the
largest single width win left in that table, and the opposite of the usual "new signal costs
columns" trade.

## Design

### The glyph map (`src/wt/report.py`)

```python
_KIND_GLYPHS = {"idea": "💡", "bug": "🐛", "improvement": "✨", "chore": "🧹"}
```

Every entry is a bare codepoint with **no U+FE0F variation selector**. That is deliberate: `⚠` is
`len 1 / cell_len 1` while `⚠️` is `len 2 / cell_len 2`, so two visually identical characters would
occupy different widths depending on which got pasted in. A test pins `len == 1` and `cell_len == 2`
for every glyph so a future edit cannot smuggle a selector in.

An unknown kind falls back to its text, so a hand-edited `:KIND:` still renders. (`idea_kind`
normalises unknown values to `idea`, so this is belt-and-braces.)

### Rendering

`ideas()` and `next_ideas()` gain a `plain` parameter, threaded from the CLI. The kind cell becomes
`prow["kind"] if plain else _KIND_GLYPHS.get(prow["kind"], prow["kind"])`, computed onto the row as
`prow["_kind"]` alongside SPEC-0077's `_age`, so `_meta_widths` measures what is actually shown —
the same pattern, for the same reason.

The footer legend appears only when glyphs are in use:

```
full text: wt idea show <id> · structured: wt ideas --json · next steps: wt next
💡 idea · 🐛 bug · ✨ improvement · 🧹 chore
```

`wt next` shows glyphs without a legend; it has no footer line, and adding one would change the
shape of a view whose purpose is the `next` column. The vocabulary is learned from `wt ideas`.

### `cell_len` in `_meta_widths` (`src/wt/report.py:551,554`)

```python
widest = max((cell_len(str(r.get(cell) or "")) for r in prows), default=0)
...
out[k] = max(min_w, cell_len(header), widest)
```

With the header kept at `kind` this changes no output — the 4 reserved cells already exceed a 2-cell
glyph. It is included because the budget is *supposed* to be display width, and it becomes
load-bearing the moment anyone shortens a header. Verified separately that Rich itself measures
correctly: a table containing emoji renders inside its console width regardless.

### CLI

`--plain` on `wt ideas` and `wt next`. A flag rather than a config key or env var: SPEC-0083 showed
an invisible toggle is worthless, and a flag is directly testable.

## Alternatives considered

- **Colour the kind column** (`IDEA-101`) — `DROPPED`. Colour is stripped for non-tty and was proven
  invisible in practice; it also returns no width.
- **Single-cell geometric symbols (`● ◆ ▲ ·`)** — `cell_len 1`, no font or width risk, and safer on
  exotic terminals. Rejected on the owner's call: emoji are self-explanatory, which materially
  reduces reliance on the legend.
- **Single letters (`i b c m`)** — maximally portable, but reads as an abbreviation rather than a
  marker and is barely more compact than the words.
- **Glyph *preceding* the word** — unambiguous, but saves nothing, and the entire width case rests
  on replacement.
- **Shorten the header to `k`** — recovers 3 more columns, rejected as cryptic; it would also make
  the `cell_len` fix mandatory rather than hygienic.
- **A config key or `$WT_PLAIN` instead of a flag** — rejected for the SPEC-0083 reason above.

## Acceptance criteria

- [x] `wt ideas` renders 💡/🐛/✨/🧹 in the `kind` column for the four kinds.
- [x] `wt ideas --plain` renders the words `idea`/`bug`/`improvement`/`chore` instead.
- [x] `wt next` and `wt next --plain` behave the same way.
- [x] Every glyph is `len() == 1` and `cell_len() == 2` — no variation selectors.
- [x] An unrecognised kind value renders as its text, not as a blank or an error.
- [x] The `kind` column is 4 cells wide with glyphs, versus 11 when `improvement` is present in
      plain mode — i.e. the headline budget grows by 7.
- [x] No rendered line exceeds the console width at widths {200, 120, 80, 60}, in glyph *and* plain
      mode (SPEC-0075's invariant, measured with `cell_len` not `len`).
- [x] All columns remain present at those widths in both modes.
- [x] The legend appears on `wt ideas` only when glyphs are in use, and not under `--plain`.
- [x] `--json` output is identical with and without `--plain`.
- [x] `_meta_widths` uses `cell_len`; a header of length 1 with a 2-cell glyph still reserves 2.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_kind_glyphs.py` (51 tests):

- `test_glyphs_have_no_variation_selectors` — `len == 1` and `cell_len == 2` for all four. The trap
  is invisible on inspection, so it is asserted mechanically.
- `test_map_covers_every_kind` — keys equal `IDEA_KINDS`, so adding a kind cannot silently fall back
  to text.
- `test_table_shows_glyphs` / `test_plain_shows_words` — for both views.
- `test_unknown_kind_falls_back_to_text`.
- `test_glyph_mode_gives_the_headline_more_width` — same rows rendered both ways; the visible
  headline is *strictly longer* in glyph mode. This is the whole justification, so it is measured
  rather than assumed.
- `test_no_line_exceeds_width` — widths {200,120,80,60} × both modes × both views, measured with
  `cell_len` (using `len` would pass while the terminal wrapped).
- `test_all_columns_present` — same matrix.
- `test_legend_shown_only_with_glyphs`.
- `test_json_unaffected_by_plain`.
- `test_meta_widths_uses_display_width` — a synthetic column with a 1-char header and a 2-cell cell
  reserves 2, which `len` would report as 1. Guards the fix directly, since the current header
  masks it.

**Manual verification**

1. `uv run wt ideas` — glyph column and footer legend
   (`💡 idea · 🐛 bug · ✨ improvement · 🧹 chore`). **Done.**
2. `uv run wt ideas --plain` — words, no legend, `kind` column back to 11 cells. **Done.**
3. **Headline gain measured, not assumed:** the same row at width 130 shows **69** headline
   characters in glyph mode against **62** plain — exactly the predicted 7. **Done.**
4. `uv run wt ideas | cat` — 30 glyphs present in piped output, 0 under `--plain`. This is the
   property that colour lacks and the reason this encoding was chosen. **Done.**
5. `uv run wt next` / `wt next --plain`. **Done.**
6. No line exceeds the console width at {200, 120, 80, 60} × both modes × both views, measured
   with `cell_len` (with `len` the check would pass while a real terminal wrapped). **Done.**

**Regression guard**

Full `uv run pytest`, especially `tests/test_idea_table_width.py`, `tests/test_idea_freshness.py`
and `tests/test_idea_state_color.py`.

## Clock Log

Clocked on IDEA-104 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

Presentation only; no data or schema change. `--plain` is the escape hatch if any terminal renders
the glyphs badly.

**Known limitation, stated rather than implied:** `kind` is 88% the default value `idea` (26 of 29
open ideas, with zero open bugs or chores), so in the default view this shows the same glyph 26
times. The 7 reclaimed columns are unconditional; the *signal* is not, and will not be until kinds
are actually chosen at capture time — `IDEA-101`'s surviving question, deliberately not closed by
this spec.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Glyph set* → emoji, on the owner's call; single-cell symbols were the safer alternative and are
  recorded above.
- *Header* → keep `kind`; saving is 7 columns, not 10.
- *Replace or precede the word* → replace; precede saves nothing.
- *Opt-out shape* → CLI `--plain`, not config or env.
- *Legend* → on `wt ideas`'s existing footer, only in glyph mode.
- *Width accounting* → `cell_len`, as hygiene now and correctness later.
