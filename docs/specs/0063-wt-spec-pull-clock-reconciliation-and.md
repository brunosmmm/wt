---
id: SPEC-0063
title: "wt spec pull-clock reconciliation and supplemental aggregation"
status: done
owner: user
created: 2026-07-25
updated: 2026-07-25
source_idea: IDEA-075
parent: SPEC-0060
milestone: "M4: cli ergonomics"
depends_on: [SPEC-0061, SPEC-0062]
tags: [time-tracking, export]
---

## Context

Third child of [SPEC-0060](./0060-agent-clock-in-clock-out-guidance-for-wt-tracked.md), on top
of [SPEC-0061](./0061-org-side-clock-in-clock-out-primitive.md) (org clock primitive) and
[SPEC-0062](./0062-markdown-clock-log-convention-and-guidance.md) (markdown `## Clock Log`
convention). This spec closes the loop: reconcile a portable spec's markdown clock log into
org `CLOCK:` entries on the linked idea, and surface clocked hours as a labeled supplemental
figure — never merged into wt's passive transcript-derived totals.

## Decision

Add `wt spec pull-clock <OUTBOUND-ID>`, mirroring `wt spec pull_status`'s shape (`export.py`):
resolve the outbox copy's `source_idea`, read the (local) portable file's `## Clock Log`,
parse complete `CLOCK-IN`/`CLOCK-OUT` pairs, and append each as a closed org `CLOCK:` entry on
the linked idea — idempotently (an identical pair already present is not re-added). Surface
total closed clock hours per idea as a supplemental panel in `wt digest`, clearly labeled and
kept separate from the existing hours-by-key table.

## Design

- **Markdown parser (`explore.py`, `parse_clock_log(text) -> list[(start, end)]`):** reads
  `CLOCK-IN: [ts]` / `CLOCK-OUT: [ts]` lines in order, pairing sequentially; an unmatched
  trailing `CLOCK-IN` (session still open) is skipped, not an error — nothing to reconcile yet.
  Timestamps parsed as ISO (`datetime.fromisoformat`), matching what an agent naturally writes
  (SPEC-0062's guidance says `[timestamp]`, not org's bracket format — markdown side is plain
  ISO, not org-native).
- **Org writer (`org_write.py`, `add_clock_entry(cfg, selector, start, end)`):** appends a
  **closed** `CLOCK: [start]--[end] => H:MM` line directly (bypassing `clock_in`/`clock_out`'s
  open/close state machine — these are historical, already-complete pairs, not a live
  session). Locates/creates `:LOGBOOK:` the same way `clock_in` does (reused via `_find_logbook`).
  Idempotent: skips appending if an identical formatted `CLOCK:` line already exists in the
  drawer (string compare on the rendered line).
- **`export.py`, `pull_clock(cfg, outbound_id, *, to=None)`:** resolve the outbox copy
  (`_find_outbound_spec`) and its `source_idea` (raise if absent — nothing to reconcile onto);
  resolve the local portable dest path (`_portable_dest_path`, same helper `pull_status` uses);
  read its `## Clock Log` via `specmeta.sections()`; `parse_clock_log`; `add_clock_entry` each
  pair onto the linked idea. Returns `(idea_id, n_added)`.
- **CLI:** `wt spec pull-clock <OUTBOUND-ID> [--to PATH]`, same `--to` override shape as
  `pull-status`.
- **Supplemental surfacing (`report.py`, `digest()`):** after the existing hours-by-key output,
  sum each idea's closed `Task.clock` durations (from `org.py`'s `Task.clock`, SPEC-0061) and,
  if any are non-zero, print one additional panel — `"Clocked (supplemental — not included in
  hours above)"` — listing idea id + heading + hours. Not scoped by the digest's day/week
  window (clock entries aren't date-filtered here); that refinement is an explicit non-goal.

## Alternatives considered

- **Fold into `wt spec pull-status`** — rejected per the epic's resolved decision: keeps status
  and clock reconciliation independently opt-in, avoids one command silently doing two things.
- **Merge clocked hours into `hours_by_key`/the passive total** — rejected per the epic's
  resolved decision: risks silently double-counting time also captured by passive transcript
  tracking for the same window: the whole point of "supplemental" is visible separation.
- **Date-scope the supplemental clock figure to `digest`'s day/week window** — deferred (not
  rejected, just out of scope for v1): would need clock entries to carry enough context to
  filter by day, adding real complexity for a "supplemental, always-visible" figure that isn't
  the primary billable number. Revisit if it proves confusing in practice.

## Acceptance criteria

- [x] `wt spec pull-clock <ID>` reads a portable spec's `## Clock Log`, resolves the linked
      idea via the outbox copy's `source_idea`, and appends matching closed `CLOCK:` entries.
- [x] Running `pull-clock` twice on unchanged input does not duplicate entries.
- [x] An outbound spec with no `source_idea` errors cleanly (nothing to reconcile onto).
- [x] An unmatched trailing `CLOCK-IN` (no paired `CLOCK-OUT`) is skipped, not an error.
- [x] `wt digest` shows a labeled supplemental panel of clocked hours per idea, visibly
      separate from the existing hours-by-key table, when any idea has closed clock time.

## Test plan

- **Automated tests** (6 new): `tests/test_clock.py` — `parse_clock_log` pairs complete
  entries and skips a trailing unmatched `CLOCK-IN`; `add_clock_entry` appends a closed line
  and is idempotent on a repeat call with the same pair. `tests/test_export.py` —
  `pull_clock` end-to-end (outbound spec with `source_idea` + a local portable Clock Log →
  matching org `CLOCK:` entries on the idea, re-run adds 0); missing `source_idea` raises
  cleanly. `tests/test_join.py` — `digest()` prints the supplemental panel with correct hours
  when clock data exists, omits it when there is none.
- **Manual verification (performed):** scaffolded a real outbound spec from an idea, exported
  it, edited the portable copy's Clock Log with a real `CLOCK-IN`/`CLOCK-OUT` pair, ran
  `pull_clock` — confirmed the linked idea's real `.org` file gained a correct `CLOCK: […]--[…]
  => 1:15` entry under `:LOGBOOK:`.
- **Regression guard:** full `uv run pytest` green; `wt digest` output for scopes/ideas with no
  clock data is byte-identical to before.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green; manual step performed.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.
