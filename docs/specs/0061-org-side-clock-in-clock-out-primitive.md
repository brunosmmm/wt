---
id: SPEC-0061
title: "Org-side clock-in/clock-out primitive"
status: done
owner: user
created: 2026-07-25
updated: 2026-07-25
source_idea: IDEA-073
parent: SPEC-0060
milestone: "M4: cli ergonomics"
tags: [time-tracking, org]
---

## Context

Foundation child of [SPEC-0060](./0060-agent-clock-in-clock-out-guidance-for-wt-tracked.md).
orgparse already parses `CLOCK:` entries under a headline's `:LOGBOOK:` drawer into
`node.clock` — including an **active** (unfinished) clock, `CLOCK: [start]` with no end,
though accessing `.duration` on one crashes (`TypeError: unsupported operand type(s) for -:
'NoneType' and 'datetime.datetime'`), confirmed by probing orgparse directly. wt has no writer
or reader for any of this today.

## Decision

Add `clock_in`/`clock_out` to `org_write.py` (same drift-guarded, atomic-write shape as
`set_state`/`set_property`), and a `Task.clock` field in `org.py` exposing parsed
`(start, end)` pairs (end `None` = still active), guarding orgparse's `.duration` crash by
never touching it — durations are computed from `(end - start)` directly when both are
present.

## Design

- **`org_write.py`:**
  - `_CLOCK_LINE_RE`: matches a `CLOCK:` line, capturing the start bracket and, optionally,
    the end bracket + duration (absent = open/active clock).
  - `clock_in(cfg, selector, *, when=None)`: resolve the idea; locate/create its `:LOGBOOK:`
    drawer (immediately after PLANNING lines and any `:PROPERTIES:` drawer — org's
    conventional order); if an open clock line already exists in the drawer, raise
    (`"already clocked in since {start}"`); else insert `CLOCK: [stamp]` before `:END:`.
    Timestamp via the existing `_inactive_stamp(cfg, when=when, with_time=True)` helper (same
    format Log entries already use).
  - `clock_out(cfg, selector, *, when=None)`: locate the drawer's open clock line (none →
    raise `"not clocked in"`); parse its start bracket (`strptime` against the same
    `_inactive_stamp` format), compute `duration = when - start` (`when` defaults to now),
    rewrite the line to `CLOCK: [start]--[end] => H:MM` (`H:MM`, unpadded hours, matching org
    convention).
  - Both drift-guard the headline (same check `set_state` already does) and use
    `_atomic_backup_write`.
- **`org.py`:** `Task.clock: tuple = ()` — populated in `_node_to_task` from `node.clock`,
  each entry `(start: datetime, end: datetime | None)`. `.duration` is never accessed (the
  crash-prone orgparse property); callers compute `end - start` themselves when `end` is not
  `None`.
- **CLI (`cli.py`):** `wt idea clock-in SELECTOR` / `wt idea clock-out SELECTOR`, mirroring
  `wt idea close`'s error handling (`ValueError` → `click.ClickException`).

## Alternatives considered

- **A single `wt idea clock SELECTOR --toggle` verb** — rejected: explicit `clock-in`/
  `clock-out` is less error-prone (no hidden state query needed to know which action a bare
  toggle will take) and matches Emacs org-mode's own `C-c C-x C-i` / `C-c C-x C-o` split.
- **Store clock state as a property instead of `:LOGBOOK:` `CLOCK:` lines** — rejected: the
  whole point is org-native interop (Emacs agenda/clock reports, orgparse) — a bespoke
  property would forgo that for no benefit.

## Acceptance criteria

- [x] `wt idea clock-in IDEA-NNN` inserts a `:LOGBOOK:` drawer (creating it if absent) with an
      open `CLOCK: [timestamp]` line.
- [x] `wt idea clock-in` on an idea already clocked in errors cleanly, no file write.
- [x] `wt idea clock-out IDEA-NNN` closes the open clock line to `CLOCK: [start]--[end] =>
      H:MM` with a correct duration.
- [x] `wt idea clock-out` with no open clock errors cleanly, no file write.
- [x] `Task.clock` exposes `(start, end)` pairs read back via orgparse for both closed and
      still-open clocks, without crashing on an open one.
- [x] A second `:LOGBOOK:` clock pair (clock-in, clock-out, clock-in again) round-trips
      correctly — the drawer accumulates entries rather than being clobbered.

## Test plan

- **Automated tests** (`tests/test_clock.py`): clock-in creates the drawer + open line;
  clock-in while already clocked in raises with no write; clock-out closes the line with a
  correct `H:MM` duration; clock-out with nothing open raises with no write; `Task.clock`
  round-trips open and closed entries; multiple clock-in/out cycles accumulate correctly in
  the same drawer.
- **Manual verification (performed):** clocked in on a real scratch idea via `org_write.clock_in`
  and inspected the resulting `.org` file directly — correct `:PROPERTIES:` then `:LOGBOOK:`
  ordering, open `CLOCK: [timestamp]` line. Emacs was not available in this environment to
  additionally spot-check with a live org buffer; the shape matches org's documented `CLOCK:`
  convention and orgparse (the library wt itself reads with) round-trips it correctly.
- **Regression guard:** full `uv run pytest` green; existing `Task` consumers unaffected by
  the new `clock` field (default `()`).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green; manual step performed.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.
