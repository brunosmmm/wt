---
id: SPEC-0077
title: "wt ideas: show an updated column and order by freshness"
status: done
owner: user
created: 2026-07-27
updated: 2026-07-27
source_idea: IDEA-092
milestone: "M4: cli ergonomics"
tags: [cli, ideas, ergonomics]
depends_on: [SPEC-0075, SPEC-0076]
---

## Context

`IDEA-092` asked for three things: drop the `next` column, widen the headline, and **add a
column showing when each idea was last updated**.
[SPEC-0075](./0075-overhaul-the-wt-ideas-triage-table-drop-the-next.md) did the first two and
declared the column out of scope because the data did not exist.
[SPEC-0076](./0076-per-idea-update-tracking-stamp-a-durable-updated.md) built the data —
`:CREATED:`/`:UPDATED:` properties, now on 74 real ideas, exposed as `created`/`updated` on
`idea_row` (`src/wt/report.py:31`) — and declared the *display* out of scope as belonging to a
SPEC-0075 follow-up that was never written.

Net effect: the third ask fell through the gap between the two specs. `wt ideas` still shows no
freshness at all, so the original request is unfulfilled. This spec closes it.

It also acts on the intent behind `IDEA-092`'s framing ("the current CLI interface is bad"),
which the earlier specs treated as decoration: with freshness available, the *default ordering*
becomes the lever that changes how the list reads. Today `wt ideas` sorts by
`_task_sort_key` — `(is_done, priority, project, heading)` (`src/wt/report.py:379`) — i.e.
alphabetically within project, which carries no signal about what is live.

## Goals / Non-goals

**Goals**

- `wt ideas` shows a compact relative age per idea (`3d`, `6w`), and an explicit placeholder
  when an idea has no stamp.
- `wt ideas` lists the most recently updated ideas first, so active thinking floats up and
  neglected ideas sink.
- Ideas with no `:UPDATED:` stamp sort last rather than sorting as infinitely old or crashing.
- The age is derived from the stamp at render time; no new stored data.

**Non-goals**

- No change to `wt next`. It keeps its own column set and ordering (`collect_next_tasks`).
- Not showing `:CREATED:`. It exists on `idea_row` but only new captures have it, so a column
  would be mostly blank; revisit when coverage is real.
- No absolute-date column, and no `--sort` flag. One default that reads well; add options only
  if the default proves wrong.
- No change to the `wt.ideas.v1` / `wt.hub.v1` schemas — `updated` is already a row field from
  SPEC-0076. Row *order* changes; field shape does not.
- Not reshaping the table into grouped sections or multi-line cards (both considered below).

## Decision

Add an `updated` column to `wt ideas` between `project` and `idea`, rendering the stamp as a
compact relative age (`2h`, `3d`, `6w`, `2y`) and `—` when absent. Change the default order of
the ideas listing to **most recently updated first**, with unstamped ideas last, keeping
not-done-before-done so `--all` still reads sensibly.

The ordering changes `collect_idea_tasks`, which backs the table, `wt ideas --json`, and the
`ideas` list in `wt hub` — so all three agree on what "the ideas list" means. `wt next` is
untouched.

## Design

### Parsing the stamp — `parse_inactive_stamp` (`src/wt/org_write.py`, beside `_inactive_stamp`)

```python
def parse_inactive_stamp(text) -> dt.datetime | None:
    """`[2026-07-27 Mon 14:03]` (or dateless `[2026-07-27]`) -> naive datetime; None if absent
    or unparseable."""
```

The write side already exists (`_inactive_stamp`, `src/wt/org_write.py:62`); this is its
inverse. `explore.newest_log_stamp` (`src/wt/explore.py`) is refactored onto it so there is one
stamp parser rather than two regexes that can drift.

Tolerant by construction: a malformed or hand-mangled property returns `None` and the idea reads
as unstamped, never raising inside a listing command.

### Rendering the age — `_age` (`src/wt/report.py`, beside `_clip`)

`_age(stamp_text, *, now)` → `""`-safe short string:

| Elapsed | Rendered |
|---|---|
| unparseable / missing | `—` |
| < 1 hour | `{m}m` |
| < 1 day | `{h}h` |
| < 7 days | `{d}d` |
| < 1 year | `{w}w` |
| otherwise | `{y}y` |

Bounded at 3–4 characters so the column costs almost nothing, which matters because SPEC-0075
made the headline the beneficiary of every spare column. A future timestamp (clock skew) renders
as `0m`, not a negative.

`now` is a parameter so tests pin exact boundaries instead of sleeping.

### Column (`report.ideas()`)

`_IDEA_META_COLS` gains `"updated": ("updated", 7, 8)` — wide enough for the header, capped just
above it. The column is added to `keys` between `project` and `idea`, so
`_meta_widths` / `_idea_table_widths` (SPEC-0075) size it with everything else and the headline
keeps whatever is left. Cells are `_age(prow.get("updated"), now=…)`, dim-styled like other
metadata.

*(As-built: `ideas()` precomputes the rendered age onto each row as `prow["_age"]`, and
`_meta_widths` measures the `updated` column from `_age` rather than from the row's `updated`
field. Measuring the raw field would have sized the column for the ~20-char stamp — capped to 8
— permanently costing the headline width that SPEC-0075 just reclaimed. A test pins the column
at <= 8.)*

*(As-built: `_age` normalizes an aware `now` to naive before subtracting. `ideas()` passes
`dt.datetime.now(cfg["_tz"])` while org stamps parse as naive local wall-clock, so the first
run raised `can't subtract offset-naive and offset-aware datetimes`. Normalizing inside `_age`
keeps every caller — including tests passing a fixed naive `now` — correct.)*

### Ordering — `_idea_freshness_key` (`src/wt/report.py`)

```python
def _idea_freshness_key(task):
    """(is_done, no_stamp, -epoch, heading) — newest first, unstamped last."""
```

- `is_done` first so `--all` keeps open ideas above `PROMOTED`/`DROPPED`.
- `no_stamp` as a boolean before the timestamp, which is what puts the 24 unstamped ideas at the
  bottom instead of treating a missing stamp as 1970.
- Negated epoch for descending recency; `heading` as a stable final tiebreaker so equal stamps
  (same-minute writes are common — SPEC-0076 stamps to the minute) never order randomly.

`collect_idea_tasks` (`src/wt/report.py:54`) swaps `_task_sort_key` for this. `_task_sort_key`
stays as-is for `wt tasks` and `collect_next_tasks`.

## Alternatives considered

- **Headline-first with collapsed trailing metadata** — genuinely more readable per row, but it
  abandons the column alignment that makes state/project scannable down the list, and it is a
  bigger visual break than the ask warrants.
- **Grouped sections per project** — best for a 41-row list, but it fights freshness ordering
  (a global "what's live" view is exactly what grouping destroys) and needs paging decisions.
- **Two-line cards** — most readable per idea, halves the ideas visible at once.
- **Absolute dates (`2026-07-24`)** — precise, but 10 columns to answer a question ("recent or
  stale?") that 2 characters answer better; the exact stamp is in `wt idea show`.
- **Sort stalest-first** — a neglect list. Useful, but the common daily use is resuming live
  work; that view can be a flag later if wanted.
- **Sort in `ideas()` only, leaving `collect_idea_tasks` alone** — rejected: the table and
  `--json` would then disagree about order for no reason.

## Acceptance criteria

- [x] `wt ideas` renders an `updated` column between `project` and `idea`; `wt next` does not.
- [x] An idea stamped minutes/hours/days/weeks/years ago renders `Nm`/`Nh`/`Nd`/`Nw`/`Ny`
      respectively, and an unstamped idea renders `—`.
- [x] A future stamp renders `0m`, never a negative or a crash.
- [x] A malformed `:UPDATED:` value renders `—` and does not raise.
- [x] `wt ideas` lists strictly newest-updated first among open ideas.
- [x] Unstamped ideas appear after every stamped idea.
- [x] With `--all`, no done idea (`PROMOTED`/`DROPPED`) appears above an open one.
- [x] Ideas with identical stamps are ordered by heading, deterministically across runs.
- [x] `wt ideas --json` rows are in the same order as the table, and every row keeps its
      existing keys (no schema change).
- [x] `wt next` ordering is unchanged.
- [x] The headline still gets the leftover width and no line exceeds the console width
      (SPEC-0075 invariants hold with the extra column).
- [x] `parse_inactive_stamp` round-trips `_inactive_stamp` output for both dated and
      date+time forms.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_idea_freshness.py` (41 tests):

- `test_updated_column_present_in_ideas_not_next` — header assertions on both tables.
- `test_age_rendering_boundaries` — unit-test `_age` with a fixed `now` at each boundary
  (59m/60m, 23h/24h, 6d/7d, 51w/52w) plus missing, malformed, and future stamps. Boundaries are
  where off-by-one bugs live, so they are pinned rather than sampled.
- `test_unstamped_renders_placeholder` — an idea with no `:UPDATED:` shows `—` in the table.
- `test_ideas_sorted_newest_first` — three ideas stamped at known distinct times; assert row
  order in the rendered table.
- `test_unstamped_sort_last` — a mix of stamped and unstamped; every unstamped id appears below
  every stamped one.
- `test_done_ideas_stay_below_open_with_all` — `--all` view keeps `DROPPED`/`PROMOTED` at the
  bottom.
- `test_equal_stamps_break_ties_by_heading` — two ideas with the identical stamp order by
  heading, and the order is the same across repeated calls.
- `test_json_order_matches_table` — the id sequence from `wt ideas --json` equals the id
  sequence rendered in the table.
- `test_next_order_unchanged` — `wt next` ids match the pre-change `_task_sort_key` order.
- `test_parse_inactive_stamp_round_trip` — `parse_inactive_stamp(_inactive_stamp(...))` for
  `with_time` True and False; plus `None` for junk.
- `test_spec_0075_invariants_hold_with_new_column` — parametrised over widths {200, 120, 80, 60}:
  all columns present, no line exceeds the width, one row per idea.

**Manual verification**

1. `uv run wt ideas` — `updated` column reads `0m`/`45m`/`1d`/`3d`/`—`, most recent at the top.
   **Done.**
2. `uv run wt idea log IDEA-088 --note "…"` then rerun — IDEA-088 moved from row 47 (`—`) to
   row 1 (`0m`). **Done.** (Its state was auto-advanced IDEA→INCUBATE by `append_log` and was
   reverted with `wt state IDEA-088 IDEA` afterwards; the verification Log entry remains.)
3. `uv run wt ideas --all` — verified against `--json` over all 98 ideas: first done row is
   index 41, last open row index 40, so no done idea sits above an open one; among open stamped
   rows the order is monotonically newest-first; every unstamped row follows every stamped one.
   **Done.** (Checked via JSON rather than by eye: several headlines contain literal `IDEA-0NN`
   text, which defeats column-position parsing of the rendered table.)
4. `uv run wt next` — header still `id state kind project next idea`, no `updated`. **Done.**

**Regression guard**

Full `uv run pytest`, including `tests/test_idea_table_width.py` (SPEC-0075's width invariants
with a sixth column now in play) and `tests/test_idea_stamps.py` (SPEC-0076's data), plus
`tests/test_json_cli.py` for the envelopes. Any test that asserted a specific `wt ideas` row
order is updated, not deleted.

## Clock Log

Clocked on IDEA-092 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

Display and ordering only; no stored data changes. The 24 ideas with no stamp read `—` until
something touches them (or `wt idea backfill-stamps` finds a new signal), which is the honest
rendering.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — the layout shape and sort direction were chosen explicitly (see Alternatives).
