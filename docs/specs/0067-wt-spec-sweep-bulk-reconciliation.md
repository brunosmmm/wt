---
id: SPEC-0067
title: "wt spec sweep: bulk pull-status/pull-clock across pending exported ideas"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-080
parent: SPEC-0064
milestone: "M4: cli ergonomics"
tags: [export, time-tracking, reliability]
depends_on: [SPEC-0065]
---

## Context

Promoted from idea `IDEA-080` (SPEC-0067).

  :PROPERTIES:
  :ID: IDEA-080
  :EPIC: SPEC-0064
  :END:
** Summary
Child of epic `SPEC-0064`.

SPEC-0067 — `wt spec sweep`: bulk pull-status/pull-clock across pending exported ideas +
** Open questions

** Log

## Goals / Non-goals

**Goals**
- Add `wt spec sweep`: enumerate every idea whose state is `EXPORTED` and whose linked outbound
  spec's `status` is not yet `done` (the "pending" set — mirrors the same status check
  `next_step_for_idea` already uses), and for each, call the existing `pull_status`/`pull_clock`
  functions to reconcile it in one bulk pass.
- On any single idea's destination being missing/unreadable, log it to that project's
  `PROVENANCE.md` and continue sweeping the rest — one bad entry must not abort the run.
- Print a clear per-idea summary (updated / unchanged / missing) so a human can see what the
  sweep actually did.

**Non-goals**
- Not auto-running `fit_log` — resolved during explore, stays a manual human-judgment step.
- Not a background/scheduled job — this is an explicit, manually invoked command, same as
  `pull-status`/`pull-clock` today.
- Not fixing the missing `pull-clock` hint in `wt next` — that's SPEC-0068, independent.

## Decision

`wt spec sweep` enumerates pending EXPORTED ideas via the existing `load_tasks`/`filter_tasks`
primitives (no new task-loading machinery), resolves each one's outbound id via its `:SPEC:`
property, and calls the existing `pull_status`/`pull_clock` functions per idea — reusing all
reconciliation logic rather than reimplementing it. A missing destination raises `ValueError`
from those functions today; the sweep catches it per-idea, appends a line to that project's
`PROVENANCE.md`, and moves on.

## Design

- **Enumeration:** `tasks = load_tasks(cfg)`; `pending = filter_tasks(tasks, state="EXPORTED",
  is_idea=True)`. For each, read `:SPEC:` from `task.properties`; skip (silently) any idea with
  no `:SPEC:` (shouldn't happen given the state, but defensive). Resolve the outbound spec's own
  `status` frontmatter field (via `_find_outbound_spec` + `split_frontmatter`, same helpers
  `pull_status` already uses) and skip ideas whose outbound status is already `"done"` — mirrors
  the exact `_DONE = frozenset({"done"})` check `workflow.py` already uses, so "pending" means
  the same thing here as it does in `wt next`'s hints.
- **Per-idea reconciliation (`export.py`, new `sweep(cfg)` function):**
  ```python
  def sweep(cfg):
      results = []  # (idea_id, outbound_id, status)
      for task in pending_exported_ideas(cfg):          # new helper, see above
          outbound_id = task.properties.get("SPEC")
          try:
              _path, status = pull_status(cfg, outbound_id)
          except ValueError as e:
              results.append((task.id, outbound_id, f"missing: {e}"))
              _log_sweep_miss(cfg, outbound_id, e)
              continue
          try:
              _idea_id, added = pull_clock(cfg, outbound_id)
          except ValueError:
              added = 0   # e.g. no source_idea on an edge-case spec; status already pulled
          results.append((task.id, outbound_id, f"status={status}, +{added} clock"))
      return results
  ```
- **Missing-destination logging (`_log_sweep_miss`):** append one line to the same
  `outbox_dir(cfg)/<project>/PROVENANCE.md` file `_append_provenance` already writes to
  (`export.py:56`), same append-only format/precedent, e.g.:
  `- {timestamp} — {outbound_id} sweep: destination missing ({error})`.
  No new storage format invented — reuses the existing per-project provenance log.
- **CLI (`cli.py`):** `wt spec sweep` (bare, no args — sweeps everything pending). Prints one
  line per idea via `console.print` (not a Rich `Table` object — simpler and sufficient for the
  expected volume of pending ideas), color-coded by result label. Exit code 0 even with misses
  (misses are logged, not fatal) — a human reviews the output/`PROVENANCE.md` for anything
  needing attention.
- **Shipped refinement over the original sketch:** `sweep()` compares the outbound spec's
  `status` before/after `pull_status` and labels each result `"updated"` (status changed or
  clock entries were added), `"unchanged"` (neither), or `"missing"` (destination gone) — this
  directly satisfies the acceptance criterion requiring the three-way distinction, which the
  original pseudocode's plain `f"status={status}, +{added} clock"` string didn't make explicit.

## Alternatives considered

- **Reimplement status/clock reconciliation inline in the sweep** — rejected: `pull_status`/
  `pull_clock` are already correct, tested, and idempotent; the sweep's only job is to iterate
  and call them, not duplicate their logic.
- **Hard-fail the whole sweep on the first missing destination** — rejected per SPEC-0064's
  explicit resolution: a moved/deleted target repo for one project shouldn't block reconciling
  every other pending idea in the same run.
- **New dedicated ledger file for misses instead of `PROVENANCE.md`** — rejected: `PROVENANCE.md`
  is already the established append-only, per-project, human-readable record of export-related
  events; a sweep miss is naturally another entry in that same story, not a new concept.

## Acceptance criteria

- [x] `wt spec sweep` reconciles status + clock for every idea in state `EXPORTED` whose linked
      outbound spec's status is not `done`, in one invocation.
- [x] An idea whose destination no longer exists on disk does not stop the sweep from
      processing the remaining pending ideas; a line is appended to that project's
      `PROVENANCE.md` describing the miss.
- [x] The sweep's printed output distinguishes updated / unchanged / missing per idea.
- [x] Ideas whose outbound spec is already `done`, or whose idea state is not `EXPORTED`
      (DROPPED/RESEARCHED/INCUBATE/etc.), are excluded from the sweep.

## Test plan

- **Automated tests:** `tests/test_export.py` — `sweep()` over a fixture set of 3 EXPORTED
  ideas (one with a valid destination + status change, one with clock data, one with its
  destination path deleted) asserts: the two valid ones reconcile correctly, the missing one is
  skipped without raising and produces a `PROVENANCE.md` entry, and a `done`-status or
  non-EXPORTED fixture idea is excluded from the pending set.
- **Manual verification:** run `wt spec sweep` against real in-flight exported ideas; confirm
  the printed table matches `wt idea show` state afterward.
- **Regression guard:** full `uv run pytest` green; running `pull-status`/`pull-clock`
  individually is unaffected by the new `sweep()` function's existence.

## Rollout / migration

1. Depends on SPEC-0065 (frozen `target_spec_path`) for `pull_status`/`pull_clock` to resolve
   reliably across config changes during the sweep's lifetime.
2. Add `pending_exported_ideas()`/`sweep()` to `export.py`, wire the `wt spec sweep` CLI command.
3. No data migration; first run simply reconciles whatever's currently pending.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- None blocking.
