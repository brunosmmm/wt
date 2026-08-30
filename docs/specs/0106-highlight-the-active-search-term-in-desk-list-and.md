---
id: SPEC-0106
title: "Highlight the active search term in desk list and detail"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
depends_on: [SPEC-0105]
milestone: "M5: interactive desk"
source_idea: IDEA-136
tags: [tui, ideas, search]
---

## Context

Promoted from `IDEA-136`. With [SPEC-0105](./0105-desk-search-bar-is-invisible-and-does-not-filter.md)
the desk filters as you type, so it shows *which* ideas matched — but not *why*. The reader
re-scans each heading and the detail prose hunting for the term they just typed.

Like SPEC-0105, this is follow-up work on the desk, not a reopened
[SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) child: that epic is `done` and its
criteria were met.

## Goals / Non-goals

**Goals**
- Highlight every occurrence of each active query token in the list heading column.
- Highlight the same tokens throughout the detail pane (heading, Summary, questions, Log).
- Highlighting is **faithful**: it marks exactly what the search matched, nothing else.
- Highlighting disappears with the query.

**Non-goals**
- Changing search ranking, tokenisation, or corpus (SPEC-0086 stands).
- A second matcher in the UI layer.
- Highlighting in the hub tab, or in classic CLI output (`wt ideas --query` keeps its snippet).
- Jump-to-next-match navigation.

## Decision

Use `rich.text.Text.highlight_words(tokens, "reverse", case_sensitive=False)` with tokens from
the search's own `tokenize_idea_query`. No new matcher: Rich's word highlighter already
implements case-insensitive substring matching, which is precisely SPEC-0086's rule.

## Design

**Fidelity.** `score_idea_match` accepts an idea when *every* whitespace token appears as a
case-insensitive **substring** of `heading + summary + questions + log`. Highlighting therefore
marks every case-insensitive occurrence of every token. A consequence worth stating: a token
highlights **inside longer words** (`tui` lights up within `intuitive`). That is correct — it is
what caused the match. Anything narrower would highlight less than the search actually used.

**Tokens come from one place.** `model.search_tokens(query)` wraps `tokenize_idea_query`, so the
UI cannot drift from the searcher. The desk owns no matching logic.

**Style is `reverse`, not a colour.** [SPEC-0083/0084](./0083-theme-adapt-the-idea-state-palette.md)
shipped a light-theme palette that was invisible on a dark terminal and had to be reverted
(`606d002`). `reverse` inverts whatever the terminal already renders, so it cannot vanish
against any background.

**Application points.**
- *List:* the heading cell is already a `Text` clipped to a measured budget; highlight after
  clipping, so spans line up with what is displayed.
- *Detail:* `_render_detail` keeps returning markup; `show_detail` converts with
  `Text.from_markup` and highlights the result. Highlighting the markup *string* would corrupt
  it — `escape()` shifts indices, and a span could land inside a `[dim]` tag.

Highlighting is applied only while `self.query` is non-empty, so clearing the search clears the
marks with it.

## Alternatives considered

- **Hand-rolled span finder** — rejected; a second matcher is exactly what drifts from the
  searcher. Rich already does substring matching.
- **A colour (yellow/green background)** — rejected on the SPEC-0083/0084 precedent.
- **Highlighting only the list** — rejected; the detail pane is where the reader confirms *why*
  an idea matched, which is the whole point.
- **Whole-word matching** — rejected as unfaithful: it would leave real matches unmarked.

## Acceptance criteria

- [x] With a query active, matching text is highlighted in the list heading column.
- [x] The same tokens are highlighted in the detail pane.
- [x] Highlight spans cover exactly the search tokens' occurrences, case-insensitively.
- [x] Clearing the query removes all highlighting.
- [x] No matcher or tokeniser is defined in the desk UI.

## Test plan

**Executed 2026-07-30.** `tests/test_tui_highlight.py` — 11 tests.

- **Fidelity (span-level, not "some styling exists"):** marked slices equal the token
  occurrences exactly; case-insensitive (`textual` marks `textual`/`Textual`/`TEXTUAL`);
  every token of a multi-token query marked; a token **inside a longer word** marked, with the
  surrounding characters asserted (`intuiti`) to prove it is the in-word hit; no query → no
  spans. One test cross-checks against the matcher itself: for each query, `score_idea_match`
  accepts the text **and** every marked slice is one of `tokenize_idea_query`'s tokens.
- **Detail pane:** marks applied to a `Text` built from `_render_detail`, asserting `[#A]`
  survives — proof the markup was not corrupted by index-shifting.
- **Live:** list cells have no spans, gain exactly one on typing, and lose it on Esc.
- **On screen:** the SVG is parsed for per-run fills; the matched run must use a fill no
  ordinary body text uses (`reverse` renders as the text taking the background colour). This is
  the end-to-end "the user can see it" check, not a state assertion.
- **Guard:** `tokenize_idea_query` / `score_idea_match` / `idea_match_snippet` / `_QUERY_SPLIT_RE`
  appear nowhere in the desk UI.

**Verified by sabotage**, since a highlighter is easy to test vacuously: disabling
`highlight_words` fails 7 of 11, and flipping it to `case_sensitive=True` — a subtly wrong
build that still highlights *something* — fails 5. Restored, all 11 pass.

- **Manual verification:** live org at 140×20 — heading cell
  `'Optional Textual packaging and wt t…'` carries one span over `Textual`; the SVG shows
  matched runs at `fill:#121212` against `#e0e0e0` body text, i.e. inverted.
- **Regression guard:** `uv run pytest` — 895 passed; SPEC-0100/0105 suites green.

## Known limitation

A heading is clipped to a **measured** budget before marking, so a match past the clip point
cannot be shown — at 100 columns `Optional Textual…` clips before `Textual`. Marking the
unclipped string would place spans at offsets the visible text does not have. The detail pane
always shows the match, so the information is never lost; widening the terminal reveals it in
the list.

## Clock Log

`wt idea clock-in/out` on IDEA-136.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
