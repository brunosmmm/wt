---
id: SPEC-0100
title: "Read-only ideas list and detail desk"
status: done
owner: user
created: 2026-07-30
updated: 2026-07-30
kind: feature
parent: SPEC-0098
depends_on: [SPEC-0099]
milestone: "M5: interactive desk"
source_idea: IDEA-130
tags: [tui, ideas]
---

## Context

Child of [SPEC-0098](./0098-light-ideas-tui-beside-classic-cli.md) (IDEA-130). First useful
desk surface: browse and expand ideas without writes.

## Goals / Non-goals

**Goals**
- Two-pane Textual UI: idea list + detail.
- List backed by `collect_idea_tasks` / `search_idea_tasks` with filter parity to `wt ideas`
  (state/kind/tag/project/workstream/priority/sort as already supported).
- Load **all** ideas; a switch shows/hides **non-active** (closed/archived/terminal states).
- Detail from `idea_show_payload`: Summary, OPEN/RESOLVED questions, Log, next-step hint
  (`next_step_for_idea`) display-only.
- Refresh and quit; minimal chrome.

**Non-goals**
- Any mutations (SPEC-0102).
- Hub tab (SPEC-0104).
- Auto-running next-step hints.
- Visual dashboard chrome / cards.

## Decision

Implement a read-only Textual desk launched by `wt tui`. Default list may prefer active ideas
visible, but the data load includes all ideas and a explicit switch reveals/hides non-active.
Reuse `idea_row` / `idea_show_payload` as view models — no parallel parsers.

## Design

**As shipped.**

*Split.* `src/wt/tui/model.py` imports **no Textual** — `DeskRow`, `DeskDetail`, `load_rows`,
`load_detail`, `split_log`, `status_line`. The whole data layer is therefore tested on a base
install, and `app.py` is a renderer with no data logic.

*Data.* `load_rows` → `search_idea_tasks` when a query is active, else `collect_idea_tasks`.
`load_detail` → `idea_show_payload` + `next_step_for_idea`. A parity test asserts the desk's
row order and membership equal `collect_idea_tasks` for both toggle states.

*Non-active predicate.* Exactly the `all_done` flag on the collectors — the done side of
`org_idea_keywords`' `|` (PROMOTED / EXPORTED / DROPPED / RESEARCHED by default). The desk never
hardcodes that vocabulary, so a custom `#+TODO` line stays honest. Archived ideas are in the
corpus already because `org_files` is a directory containing `ideas-archive.org`. Default view
is active-only, matching `wt ideas`. **Query mode ignores the toggle** — `search_idea_tasks`
always scans open+closed, same as `wt ideas --query`.

*Widgets.* `DataTable` (list) | `VerticalScroll`+`Static` (detail), `border-left` between them.
Columns `id st p k upd idea`. **`project` and the spelled-out state are deliberately absent** —
the first cut listed them and produced an unscannable column of bare ids; both already appear in
the detail pane, so the list spends its width on the heading (SPEC-0075's call).

*Two width bugs found by rendering, both now regression-tested:*
1. A `35%` list pane silently dropped the last column at 100 cols → pane is `50%` with
   `min-width: 40`.
2. `table.size.width` is **0 during `on_mount`** (pre-layout), which clipped headings to 12
   chars and wasted ~30 columns at 120 wide → `reload()` (reads org) is split from `paint()`
   (renders at measured width); `on_mount` paints via `call_after_refresh`, and `on_resize`
   re-clips without re-reading org.

*Detail rendering.* Rich markup with **every interpolated value `escape()`d** — org prose is
full of `[#A]`, `[[IDEA-042]]` and `[2026-07-30 Thu]`, all of which Rich would otherwise eat.
Section headers carry their own divider (`Summary ─────`) sized to the measured pane, degrading
to a bare label when too narrow.

*Bindings.* `j/k`+arrows move, `/` search (Enter applies, Esc closes and clears an applied
query), `a` toggle non-active, `r` refresh, `q` quit. No Enter-to-select: highlight *is*
selection, so the detail pane always matches the cursor.

*Filters.* Passed as `wt tui` flags (`--state/--kind/--tag/--project/--workstream/--priority/
--sort/--desc/--all/--query`) so the desk can open pre-filtered; only search + the non-active
toggle are in-app controls. In-app filter widgets would be the chrome SPEC-0098 forbids.

## Alternatives considered

- **Open-ideas-only** — rejected (epic Q2).
- **Scraping Rich tables** — rejected; call library APIs.

## Acceptance criteria

- [x] `wt tui` shows a two-pane ideas desk (requires SPEC-0099).
- [x] User can search/filter and select an idea to see Summary / questions / Log / next hint.
- [x] Switch toggles visibility of non-active ideas; all ideas are loadable.
- [x] No write paths in this spec's UI.
- [x] Classic CLI unchanged.

## Test plan

**Executed 2026-07-30.** `tests/test_tui_desk.py` — 18 tests, 11 of which need no Textual.

- **View models (base install):** log splitting (incl. the string-vs-list regression), active-only
  default vs toggle, **parity with `collect_idea_tasks`**, presentation cells, filter pass-through,
  query ranking over closed ideas, status line, question split by lowercase state, summary/log/hint.
- **Rendering:** `_render_detail` escaping — `[[IDEA-042]]` / `[#A]` / `[bold]not bold[/bold]` /
  `[2026-07-30 Thu 17:00]` all survive to the output.
- **Pilot smoke:** list→detail render asserted against a **character grid reconstructed from
  Textual's SVG export** (`_grid`; there is no `App.export_text()` and rasterizing needs a
  renderer this repo doesn't depend on, so runs are placed by column — Rich omits
  whitespace-only runs, which otherwise collapses the pane gutter). Covers: non-active hidden by
  default → `a` reveals → `a` hides; `/` search applies then Esc clears; `j` moves selection and
  repaints detail; heading present and its budget **grows** from 80→140 cols.
- **Read-only guard:** the app module is asserted to contain no mutator name and no `subprocess`.
- **CLI wiring:** every filter flag reaches `T.run`.
- **Manual verification:** rendered against the live org (43 ideas) at 100×30, 120×22 and 80×18
  and read the grid each time — this is what caught the missing-heading design error and both
  width bugs. Not attached to an interactive TTY in this session; keyboard paths are covered by
  the pilot instead.
- **Regression guard:** `uv run pytest` — 788 passed. Base install (no extra): the 7 Textual
  tests skip, rest green.

## Clock Log

`wt idea clock-in/out` on IDEA-130 (org LOGBOOK, not mirrored here).

## Rollout / migration

After SPEC-0099. Partial delivery is useful alone.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass; manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none)
