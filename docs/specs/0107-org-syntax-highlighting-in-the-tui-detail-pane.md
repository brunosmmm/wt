---
id: SPEC-0107
title: "Org syntax highlighting in the TUI detail pane"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
depends_on: [SPEC-0100, SPEC-0106]
milestone: "M5: interactive desk"
source_idea: IDEA-137
tags: [tui, org, render]
---

## Context

Promoted from `IDEA-137` with all five open questions resolved on the idea first.

The desk detail pane and `wt idea show` are **two renderings of the same content**. The CLI
already lexes org through Pygments ([SPEC-0035](./0035-pretty-wt-idea-show-via-rich-and-pygments-with.md)
/ [SPEC-0036](./0036-configurable-theme-for-pretty-idea-show.md)); the TUI hand-rolls Rich
markup in `_render_detail` ([SPEC-0100](./0100-read-only-ideas-list-and-detail-desk.md)). The
visible symptom is that the TUI is unstyled; the real cost is that only one of the two is themed.

Follow-up work on the desk, deliberately not a child of the closed
[SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) epic — same reasoning as SPEC-0105/0106.

**Verified before deciding** (2026-07-30, in-session):

- Pygments 2.20 ships `OrgLexer`, already a transitive dependency via Rich.
- `Syntax.highlight(src)` returns a Rich **`Text`**, and `Text.highlight_words` composes on top
  of it (18 lexer spans + 1 search mark = 19). SPEC-0106's marks survive lexing — this is what
  made the feature worth pursuing at all.
- `OrgLexer` emits `Generic.Heading`, `Generic.Subheading`, `Generic.Strong`, `Generic.Emph`,
  `Name.Decorator` (tags), `Literal.String` (`~code~` / `=verbatim=`), `Name.Attribute`
  (property keys), `Comment.Special` and `Keyword`.
- `nord` / `monokai` emit **hardcoded hex** (`#88c0d0`, `#f8f8f2`); `ansi_dark` / `ansi_light`
  emit **named ANSI colours** (`bold`, `yellow`) that the terminal resolves from its own palette.

## Goals / Non-goals

**Goals**
- Lex the **prose** of the detail pane — Summary, question text, Log bodies — through `OrgLexer`.
- Keep every structural affordance the desk already has.
- Theme adaptively, so no colour can be invisible on the user's background.
- SPEC-0106 search marks still render on top of lexed text.

**Non-goals**
- Showing raw org source in the detail pane (Q1, rejected).
- Converging `wt idea show` and the TUI onto one renderer (Q5, rejected for now).
- Any org *editor* affordance — fold, images, inline edit. SPEC-0035's non-goal stands.
- Lexing the list pane, the hub tab, or changing `wt idea show`.
- Fixing the CLI's own `nord` default (noted below, out of scope).

## Decision

**Keep the structured pane; lex only the prose blocks.** Structure — section rules, `○`/`✓`
question glyphs, the clock and meta lines, the next-step hint — is built *outside* the lexed
spans and never passes through Pygments. Prose runs through `OrgLexer` and comes back as `Text`,
which the existing `_mark_into` then highlights for the active search.

**Theme adaptively.** Use `ansi_dark` / `ansi_light`, selected from Textual's light/dark state,
**not** a hex Pygments theme and **not** the CLI's `idea_show_theme`.

## Design

Resolutions carried from IDEA-137, with the reasoning that produced them:

1. **Structure survives by construction** (Q1, Q3). Nothing structural is handed to the lexer,
   so there is no way for a theme to eat a section rule or a glyph. The lexer sees prose only.
2. **ANSI over hex** (Q2). A hex theme is exactly what got
   [SPEC-0083/0084](./0084-theme-every-recessive-style-in-the-idea-views.md) reverted in
   `606d002` — a palette invisible on a dark terminal. ANSI-named colours are resolved by the
   terminal, so they inherit whatever contrast the user already has. The cost is a smaller
   palette, which is the right trade for a triage surface.
3. **`OrgLexer` earns its place — but less than Context implied** (Q4). The idea's seed note
   called it "largely bold headlines + italic tags", which I corrected to a longer token list
   before deciding. **Measuring again during implementation, that correction was itself too
   generous.** Those token types appear across a whole org *document*; inside the **prose
   fragments this spec actually lexes**, only `~code~` / `=verbatim=` and links are styled —
   mid-prose `*bold*` and `/italic/` are not marked at all, and tags/property keys live on
   headlines and drawers, which are hand-built structure we deliberately never lex.

   The feature still earns its place, because `wt` prose is dense with `~tildes~` (SPEC-0030
   normalises Markdown backticks into them), but the honest scope is **code, verbatim and
   links** — not "emphasis and everything else". Asserted as a known limitation in the tests
   rather than left as a surprise.
4. **No convergence** (Q5). One shared renderer would fix the drift at its root but requires
   superseding SPEC-0035 for a payoff that is mostly internal tidiness. The two renderers stay,
   and the divergence stays written down rather than hidden. Revisit only if they visibly
   disagree.

**Shape.** A helper that takes a prose string and returns a lexed `Text`, applied where
`_render_detail` currently emits escaped prose. Since `_render_detail` returns markup today,
either it changes to assemble `Text` directly or the lexed spans are merged after
`Text.from_markup` — an implementation choice, not a design one, but the constraint is fixed:
**marks are never applied to a markup string**, because `escape()` shifts indices (SPEC-0106).

## Alternatives considered

- **Full `Syntax` on the org source** — rejected (Q1): converges with the CLI and is the least
  code, but discards structure SPEC-0100/0103 added deliberately.
- **One shared renderer for CLI + TUI** — rejected for now (Q5); would supersede SPEC-0035.
- **Reuse `idea_show_theme` (nord)** — rejected (Q2): identical look to the CLI, but inherits
  the hardcoded-hex contrast risk.
- **A new TUI-specific theme config key** — deferred; adds a knob before anyone has asked for
  one. `ansi_dark`/`ansi_light` is the default with no configuration at all.
- **Do nothing** — rejected once Q4's premise was measured and turned out understated.

## Acceptance criteria

- [x] Summary, question text and Log bodies render with org token styling in the detail pane
      (scope: `~code~` / `=verbatim=` / links — see Design point 3).
- [x] Section rules, `○`/`✓` glyphs, clock line, meta line and next-step hint are unchanged.
- [x] Styling uses ANSI-named colours; no hardcoded hex is introduced.
- [x] SPEC-0106 search marks still appear, on top of lexed prose.
- [x] `wt idea show` output is byte-identical to before.

## Test plan

**Executed 2026-07-30.** `tests/test_tui_org_syntax.py` — 13 tests.

- **What is styled:** `~code~` and `=verbatim=` carry a style; **and an explicit test asserts
  mid-prose `*bold*` / `/italic/` are *not* styled**, so the limitation is a recorded state
  rather than a surprise. Lexed prose is asserted byte-identical to its source — styling must
  never rewrite what the user typed.
- **Structure never reaches the lexer:** section rules, `○`/`✓` glyphs, the `N open · N
  resolved` note, clock and meta lines all present after lexing.
- **Markup safety:** `[#A]`, `[bold]not bold[/bold]`, `[[IDEA-042]]` and `[2026-07-30 Thu]` all
  survive intact.
- **No hardcoded colour:** every style in a rendered pane is regex-checked for `#rrggbb` under
  **both** `ansi_dark` and `ansi_light`; a source guard rejects `"nord"` / `"monokai"` /
  `"idea_show_theme"` as *string literals* (the module comments name them deliberately, to
  record why they were rejected); `syntax_theme` follows the app's light/dark state.
- **Composition:** with a query active, marking a lexed pane *adds* spans on top of the lexer's
  and every `reverse` span covers the query — SPEC-0106 survives SPEC-0107.
- **CLI untouched:** `wt idea show` still prints its own output and `format_idea_show` still
  returns a `str`.
- **Manual verification:** live org at 110×16 — Summary renders `~h~` and
  `~active=tab-hub hub_rows=0 cols=0~` styled, with the section rule, glyphs and clock line
  intact; switching `app.theme` between `textual-dark` and `textual-light` flips `syntax_theme`
  to `ansi_dark` / `ansi_light`.
- **Regression guard:** `uv run pytest` — 931 passed; SPEC-0100/0103/0105/0106 desk suites green.

One existing test changed shape: `test_detail_body_is_marked_without_corrupting_markup` no
longer wraps `_render_detail` in `Text.from_markup`, because the function now returns a `Text`.

## Rollout / migration

Read-surface only; no data or config migration. Landable independently of anything else.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — all five resolved on IDEA-137 before promotion)

## Noted, out of scope

`wt idea show` defaults to `theme: nord`, hardcoded hex, so the **CLI** carries the same
low-contrast risk on an unanticipated terminal background. Worth its own idea; not this spec.
