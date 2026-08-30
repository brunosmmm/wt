---
id: SPEC-0068
title: "wt next pull-clock hint, parity with the existing pull-status hint"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-081
parent: SPEC-0064
milestone: "M4: cli ergonomics"
tags: [time-tracking, cli]
---

## Context

Promoted from idea `IDEA-081` (SPEC-0068).

  :PROPERTIES:
  :ID: IDEA-081
  :EPIC: SPEC-0064
  :END:
** Summary
Child of epic `SPEC-0064`.

SPEC-0068 — `wt next` pull-clock hint, parity with the existing pull-status hint
** Open questions

** Log

## Goals / Non-goals

**Goals**
- `wt next`/`wt ideas`' next-step hint for an EXPORTED idea whose outbound spec's status is
  `in-progress` currently only suggests `wt spec pull-status {id}` — add an equivalent nudge
  toward `wt spec pull-clock {id}`, since nothing today points at it (confirmed by grep: it
  appears nowhere in `workflow.py`/`report.py`, only in the command definition itself).

**Non-goals**
- Not building the bulk sweep (SPEC-0067) — this is the single-idea hint only, independent of
  and no dependency on the sweep landing.
- Not changing the hint's trigger condition — same `state == "EXPORTED" and status ==
  "in-progress"` gate the existing pull-status hint already uses.

## Decision

Combine both hints into the one `next` string `next_step_for_idea` already returns for this
branch, rather than changing its return type to multiple values — `next` is a single free-text
field consumed as-is by the Rich table and `wt.next.v1` JSON (`report.py`), and nothing
downstream parses it as an exact single command.

## Design

- **`workflow.py::next_step_for_idea()`, the `in-progress` branch (~L184-185):**
  ```python
  if status == "in-progress":
      return f"wt spec pull-status {spec_id}"
  ```
  becomes:
  ```python
  if status == "in-progress":
      return f"wt spec pull-status/pull-clock {spec_id}"
  ```
  Kept as one readable compound string rather than inventing shell syntax (`&&`) or restructuring
  the function's return type — `next` is already routinely truncated in table display
  (`_clip(prow["next"], 22..24)` in `report.py`) for long spec IDs today, so this is consistent
  with existing display behavior; full text remains available via `--json` or `wt idea show`.

## Alternatives considered

- **Return a list of hints instead of one string** — rejected: would require changing the
  `wt.next.v1` JSON schema and every consumer (Rich table columns, any skill reading the JSON);
  far more invasive than the actual problem warrants for a one-line reminder.
- **Only show the pull-clock hint if the portable spec actually has unreconciled Clock Log
  entries** — rejected as unnecessary complexity: checking that would require reading the
  destination file from the hint code path (which today is a pure, fast, local computation over
  already-loaded frontmatter); reusing the same trigger as pull-status keeps it consistent and
  simple, and running `pull-clock` on an idea with nothing new to reconcile is already a
  harmless no-op (idempotent).

## Acceptance criteria

- [x] An EXPORTED idea whose outbound spec status is `in-progress` shows a next-step hint that
      mentions both `pull-status` and `pull-clock` for that spec id.
- [x] All other branches of `next_step_for_idea` are unchanged (only the `in-progress` outbound
      branch is touched).

## Test plan

- **Automated tests:** `tests/test_workflow.py` — a fixture EXPORTED idea with an `in-progress`
  outbound spec returns the combined hint string from `next_step_for_idea`; other branches
  (authxx/ready/done/review) assert unchanged output (regression).
- **Manual verification:** `wt next` against a real EXPORTED/in-progress idea; confirm the
  printed hint mentions both commands.
- **Regression guard:** full `uv run pytest` green; `wt.next.v1`/`wt.ideas` JSON schema
  unchanged (still a single `next` string field).

## Rollout / migration

1. One-line change to `next_step_for_idea`'s `in-progress` branch; no data migration, no
   dependency on the other three child specs.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- None blocking.
