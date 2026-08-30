---
id: SPEC-0075
title: "Readable idea tables: drop the next column, budget headline width from the terminal"
status: done
owner: user
created: 2026-07-27
updated: 2026-07-27
source_idea: IDEA-092
milestone: "M4: cli ergonomics"
tags: [cli, ideas, ergonomics]
---

## Context

Promoted from idea `IDEA-092`. The triage tables are unreadable: `wt ideas` caps every
headline at **40 characters regardless of terminal width**, so the column that carries the
actual information is the one that gets starved.

`report.ideas()` (`src/wt/report.py:434`) renders six columns — id / state / kind / project /
next / idea. Every column is declared `no_wrap=True` with a `min_width`, and every cell is
pre-truncated by the hand-rolled `_clip()` (`src/wt/report.py:424`) at a **hard-coded** width:
kind 12, project 16, next 22, idea **40**. Nothing in the function ever consults
`console.width`, so a 200-column terminal renders exactly the same 40 characters of headline
as an 80-column one. `report.next_ideas()` (`src/wt/report.py:473`) is a near-duplicate of the
same table with the same 40-char cap.

Two findings from the exploration shape the decision below:

- **`$COLUMNS` already works.** `console` is a bare module-level `Console()`
  (`src/wt/console.py:4`), and Rich's own `Console.size` consults `$COLUMNS` when stdout is not
  a tty. Verified: `COLUMNS=200` yields `console.width == 200` in a piped subprocess, versus
  `80` with `COLUMNS` unset. Piping is therefore already controllable and needs **no code
  change** — but the width it provides is currently thrown away by the 40-char clip. Verified
  end-to-end: `COLUMNS=200 wt ideas | cat` widens the table while headlines still stop at 40.
- **The naive fix regresses the table.** The idea assumed "delete the clip and let Rich flex
  the column". Prototyped and measured: a `no_wrap=True, overflow="ellipsis"` column with no
  upper bound makes Rich steal space from its neighbours — at width 80 and 60 the **`kind`
  column collapses to zero width and disappears entirely**, and the headline is cropped
  **without any `…` marker**, so truncation becomes invisible. Today's code renders all six
  columns at width 80. Adding `min_width` to the flexible column does not prevent the
  collapse. Pure Rich flex is therefore rejected in favour of an explicit width budget.

The third original ask — a "last updated" column — was forked to `IDEA-094` (per-idea
`:UPDATED:`/`:CREATED:` stamping); it needs a property substrate that does not exist yet and is
out of scope here.

## Goals / Non-goals

**Goals**

- Headlines in `wt ideas` and `wt next` use the full terminal width instead of a hard-coded
  40 characters.
- Drop the `next` column from `wt ideas` (`wt next` is the dedicated view for that hint).
- Every column present today stays present at every terminal width; truncation is always
  marked with `…`.
- Width behaviour is a deterministic function of `console.width` and row content, so it is
  unit-testable without a tty.

**Non-goals**

- No new `--width` CLI flag. `$COLUMNS` already covers the non-tty case and is verified.
- No change to `console.py` or the shared `Console` instance.
- No change to any JSON schema. `next` stays in the `idea_row` payload
  (`src/wt/report.py:31`), so `wt.ideas.v1` / `wt.next.v1` / `wt hub` consumers are untouched;
  this is a display-only removal.
- No change to row selection or sort order (`_task_sort_key`, `src/wt/report.py:379`).
- Not adding the last-updated column (`IDEA-094`).
- Not refactoring `ideas()` and `next_ideas()` into one shared table builder — the duplication
  is real but out of scope; both get the same fix independently.
- No change to `wt tasks` or any other table.

## Decision

Replace the hard-coded `40` headline clip with a **computed width budget**: measure what the
fixed metadata columns actually need for the rows being rendered, subtract that plus table
chrome from `console.width`, and give the entire remainder to the headline. Keep `_clip()` and
keep every column `no_wrap` — so no column can collapse and truncation always shows `…`.

Drop the `next` column from `wt ideas` only; `wt next` keeps it (it is that command's whole
point) and gets the same headline budget. `$COLUMNS` support is documented and pinned by a
regression test, not implemented — Rich already provides it.

## Design

### New helpers (`src/wt/report.py`, beside `_clip`)

`_IDEA_META_COLS` maps each metadata column to `(header, min_width, cap)` — the existing
constants: id 8/–, state 8/–, kind 4/12, project 6/16, next 10/22.

`_meta_widths(prows, keys)` returns the width each metadata column needs:
`max(min_width, len(header), min(cap, widest_cell))`, so narrow data does not reserve space it
will not use — a table where every kind is `idea` reserves 4, not 12.

`_idea_table_widths(prows, keys, *, floor=12)` returns `(widths, budget)`. Pure apart from
reading `console.width`, so it is unit-testable without rendering, and reading the width at
call time is what makes `$COLUMNS` and terminal resizes take effect.

- Table chrome for `box.SIMPLE_HEAVY` + `pad_edge=False` is **`3 * ncols - 1`**: two padding
  spaces per column plus one separator between adjacent columns. *(As-built: the draft said
  `2 * ncols - 2`. Measured against Rich by bisecting the largest uncropped headline at
  several widths — the real constant is `3n - 1` for both the 5- and 6-column tables. The
  wrong formula overestimated the budget by 6, and Rich then cropped the headline **with no
  `…`**, i.e. the exact silent-truncation failure this spec set out to avoid.)*
- The headline column also carries `overflow="ellipsis"` as a safety net, so any future Rich
  change to that arithmetic shows up as a visible `…` one column early rather than a silent
  crop.
- **Reclaim instead of over-promise.** *(As-built.)* When the terminal cannot give the headline
  `floor` (12) characters, width is taken from the widest *capped* metadata column
  (kind/project/next) down to its `min_width`, never from id/state. The draft's plan — floor the
  budget and let Rich shrink the metadata columns — was wrong in the same way: asking for 12
  when only 4 exist makes Rich crop the row mid-cell with no marker. Reclaiming keeps every
  column present and every truncation marked down to ~50 columns.

### `ideas()` (`src/wt/report.py:434`)

- Remove the `next` column: delete its `t.add_column("next", …)` and its `_clip(prow["next"],
  22)` cell. `idea_row()` is unchanged, so `--json` still carries `next`.
- Precompute `prows = [idea_row(cfg, tk) for tk in rows]` once (same number of `idea_row`
  calls as before), then `widths, budget = _idea_table_widths(prows, keys)` and clip headlines
  with `_clip(prow["heading"], budget)` in place of `_clip(prow["heading"], 40)`.
- Every metadata column is added with `min_width=widths[k]` and its cell clipped to the same
  value, so a column can neither collapse nor grow past its plan. The `idea` column keeps
  `no_wrap=True`, loses `min_width=10`, and gains `overflow="ellipsis"`.

### `next_ideas()` (`src/wt/report.py:473`)

Same change, `next` column retained (six columns). Its 40-char cap becomes the computed
budget and its 24-char `next` clip becomes `widths["next"]`.

### Docstrings and docs

- `src/wt/cli.py:558` — "List ideas (with a next-step column)" is now false; reword and point
  at `wt next`.
- `src/wt/report.py:438` and `:475` — describe the width budget; note `next` remains in JSON.
- `docs/WORKFLOW.md` — where it describes the `wt ideas` next column, note the hint now lives
  on `wt next`, and mention `COLUMNS=N wt ideas | less -S` for piping.

## Alternatives considered

- **Let Rich flex the column (`overflow="ellipsis"`, no cap)** — what the idea originally
  assumed. Rejected on measurement: the `kind` column collapses to zero width at ≤80 columns
  and truncation loses its `…` marker. Adding `min_width` to the flexible column does not fix
  it.
- **Add a `--width N` flag** — rejected as redundant CLI surface: `$COLUMNS` already works and
  needs no code.
- **Teach `console.py` to read `$COLUMNS`** — rejected as a no-op; Rich already does it, and it
  would touch a module shared by every `wt` command for no gain.
- **Keep `next` in `wt ideas` and only widen the headline** — rejected: `next` costs ~22
  columns to duplicate what `wt next` shows, and freeing it is most of the readability win.
- **Factor one shared table builder for both tables** — deferred. Worth doing, but it widens
  this diff beyond a readability fix.
- **Drop `kind`/`project` instead of `next`** — rejected: both are cheap (4–16 chars) and are
  the columns people filter on.

## Acceptance criteria

- [x] `wt ideas` renders **no** `next` column; `wt next` still renders one.
- [x] `wt ideas --json` and `wt next --json` still include a `next` field for every row, with
      identical values to before the change (no schema change).
- [x] At `COLUMNS=200`, a headline longer than 40 characters renders with **more than 40**
      characters visible in both `wt ideas` and `wt next` — the 40-char cap is gone.
- [x] At every width in {200, 120, 80, 60}, both tables render **all** their columns; the
      `kind` column never disappears.
- [x] No rendered line exceeds `console.width`, and no cell wraps onto a second line, at any of
      those widths.
- [x] Any truncated cell ends with `…`; truncation is never silent.
- [x] `_headline_budget` reserves only what the data needs: with all-short `kind`/`project`
      values the headline budget is strictly larger than with values at the 12/16 caps.
- [x] `COLUMNS=200 wt ideas | cat` (non-tty) uses the full 200 columns.
- [x] Row selection and ordering are unchanged (`collect_idea_tasks` / `_task_sort_key`
      untouched).
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_idea_table_width.py` (35 tests), plus updates to the two
pre-existing tests that asserted the removed behaviour:

- `test_ideas_table_has_no_next_column` — capture `wt ideas` at width 200; assert the `next`
  header is absent, and that a seeded long headline appears with >40 characters. Replaces the
  existing `assert "next" in r2.output.lower()` at `tests/test_ideas.py:395`, which asserts the
  behaviour this spec removes.
- `test_next_table_keeps_next_column` — `wt next` at width 200 still shows the `next` header
  and a >40-char headline.
- `test_json_still_carries_next` — `wt ideas --json` and `wt next --json` include `next` per
  row (guards the schema promise).
- `test_tables_keep_all_columns_when_narrow` — parametrised over widths {200, 120, 80, 60}:
  every expected header (`id`, `state`, `kind`, `project`, `idea`, plus `next` for `wt next`)
  is present. This is the regression guard for the column-collapse failure that rejected the
  Rich-flex alternative.
- `test_tables_never_exceed_console_width` — same widths; assert `max(len(line) for line in
  output.splitlines()) <= width` and that the row count equals the idea count (proves nothing
  wrapped).
- `test_headline_budget_scales_with_data` — unit-test `_headline_budget` directly: short
  `kind`/`project` data yields a larger budget than data at the caps, and the result never
  drops below the floor at tiny widths.
- `test_columns_env_var_controls_width` — run the CLI via `subprocess` with `COLUMNS=200` and a
  non-tty stdout; assert the output is wider than 80 columns. Pins the Rich behaviour this
  spec depends on but does not own, so a Rich upgrade that drops `$COLUMNS` fails loudly here
  rather than silently degrading piping.

**Manual verification**

1. `uv run wt ideas` in a wide terminal — headlines read much further than 40 chars, no `next`
   column.
2. Resize to ~80 columns and rerun — all five columns still present, headlines end in `…`.
3. `COLUMNS=200 uv run wt ideas | less -S` — full 200-column width.
4. `uv run wt next` — `next` column present, headline also widened.

**Regression guard**

The full suite (`uv run pytest`) must pass; `tests/test_json_cli.py` covers the JSON envelopes
and must be unaffected, which is the check that the display-only removal did not leak into
`wt.ideas.v1` / `wt.next.v1`. `tools/spec_lint.py` keeps the ledger honest.

## Clock Log

Clocked on the linked idea IDEA-092 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

No migration — display-only, no persisted data or schema touched. Single commit: helper +
both call sites + docstrings + tests. Revert is a straight revert.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Non-tty width* → use `$COLUMNS` (already works; test-pinned, no code).
- *Does `wt next` get the same treatment* → yes, headline budget only; it keeps `next`.
- *Does `next` stay in JSON* → yes, display-only removal.
- *Should `kind`/`project` also flex* → no; they stay capped at 12/16 but now reserve only what
  the data needs.
- *Sort order* → unchanged; revisit if `IDEA-094` lands a freshness field.
