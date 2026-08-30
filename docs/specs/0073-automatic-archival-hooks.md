---
id: SPEC-0073
title: "Automatic archival hooks: set_state terminal states + pull_status EXPORTED-done"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-085
parent: SPEC-0070
milestone: "M4: cli ergonomics"
tags: [org, maintenance]
depends_on: [SPEC-0072]
---

## Context

Promoted from idea `IDEA-085` (SPEC-0073).

  :PROPERTIES:
  :ID: IDEA-085
  :EPIC: SPEC-0070
  :END:
** Summary
Child of epic `SPEC-0070`.

SPEC-0073 — Automatic archival hooks: wire `archive_idea` into `set_state`'s terminal
** Open questions

** Log

## Goals / Non-goals

**Goals**
- Wire `archive_idea` (SPEC-0072) into `org_write.py::set_state()`: the moment an idea
  transitions into `DROPPED`, `RESEARCHED`, or `PROMOTED`, archive it automatically —
  covers `wt idea close` (drop/researched) and `wt spec generate`'s promotion path.
- Wire the same primitive into `export.py::pull_status()` for the one terminal condition
  that never goes through `set_state`: an `EXPORTED` idea whose linked outbound spec's status
  is *pulled* as `done` for the first time. (`sweep`, SPEC-0067, calls `pull_status`
  internally, so it inherits this automatically — no separate change needed there.)
- Zero new command surface — both hooks are side effects of existing, already-automatic code
  paths.

**Non-goals**
- Not archiving on every `set_state` call — only the three specific terminal states trigger
  it; everything else (IDEA→INCUBATE, →SPECCED, EXPORTED itself, etc.) is unaffected.
- Not making archival failure fatal to the primary operation it's attached to — if
  `pull_status` can't resolve or archive the linked idea for some reason, `pull_status` itself
  must still succeed (status reconciliation is the contract; archival is a side effect).
- Not re-archiving an idea that's already been archived — the transition-guard (only fire when
  status *changes to* `done`, not merely *is* `done`) prevents redundant no-op moves on repeat
  `pull_status`/`sweep` calls.

## Decision

Add a hardcoded `_ARCHIVE_ON_STATES = frozenset({"DROPPED", "RESEARCHED", "PROMOTED"})` check
at the end of `set_state()`, right after its existing write succeeds: if the task is an idea
and `new_state` is in that set, re-resolve the task fresh (its in-memory `state` is now stale
relative to what was just written) and call `archive_idea`. In `pull_status`, capture the
outbound spec's status *before* the pull; if the newly pulled status is `"done"` and it wasn't
already `"done"`, resolve the linked idea (reusing SPEC-0069's `_resolve_source_idea` helper)
and archive it if it's still `EXPORTED` — wrapped so a resolution/archival failure only warns,
never breaks `pull_status`'s own return value.

## Design

- **`org_write.py::set_state()`**, appended just before its `return task.file`:
  ```python
  _ARCHIVE_ON_STATES = frozenset({"DROPPED", "RESEARCHED", "PROMOTED"})
  ...
  if task.is_idea and new_state in _ARCHIVE_ON_STATES:
      fresh = resolve_selector(cfg, task.properties.get("ID") or task.id)
      archive_idea(cfg, fresh)
  ```
  Re-resolving is required because `task.state` in memory still reflects the *old* state —
  passing the stale `task` object straight to `archive_idea` would trip its own drift guard
  (it compares `task.state` against what's now actually on disk, which just changed to
  `new_state`).
- **`export.py::pull_status()`**: capture `status_before = fm.get("status")` at the top
  (before the pull); after the existing status write succeeds, add:
  ```python
  if status == "done" and status_before != "done":
      try:
          selector = _resolve_source_idea(cfg, outbound_id)
          idea = resolve_selector(cfg, selector)
          if idea.is_idea and idea.state == "EXPORTED":
              OW.archive_idea(cfg, idea)
      except ValueError as e:
          print(f"  ! {outbound_id}: could not auto-archive linked idea ({e})",
                file=sys.stderr)
  ```
  Reuses `_resolve_source_idea` (SPEC-0069) rather than duplicating idea-resolution logic.
- **`sweep()` (SPEC-0067)** needs no direct change — it already calls `pull_status` per idea,
  so the new archival side effect is inherited automatically.

## Alternatives considered

- **A single generic "any state transition" hook instead of an explicit allow-list** —
  rejected: archiving on e.g. `IDEA`→`INCUBATE` or a re-promote would be actively wrong; an
  explicit terminal-states set is the correct scope and self-documents which transitions matter.
- **Make archival failure inside `pull_status` raise instead of warn** — rejected: the user's
  actual goal in calling `pull_status`/`sweep` is reconciling status/clock data; a housekeeping
  side effect failing shouldn't block that. Matches SPEC-0067's own precedent (missing
  destinations are logged, not fatal).

## Acceptance criteria

- [x] `wt idea close <id> --as drop` (or `--as researched`) archives the idea automatically —
      it's discoverable afterward only in the archive file, not the active one.
- [x] Promoting an idea to `PROMOTED` (via the internal generate path) archives it
      automatically.
- [x] Pulling a `done` status for the first time on an `EXPORTED` idea archives it
      automatically; pulling `pull_status`/`sweep` again afterward does not re-archive or error.
- [x] A `pull_status` call whose linked idea can't be resolved (or is already archived/
      ambiguous) still returns its normal `(path, status)` result — archival failure doesn't
      propagate as a `pull_status` failure.
- [x] No other state transition (e.g. `IDEA`→`INCUBATE`, →`SPECCED`, plain `EXPORTED`) triggers
      archival.

## Test plan

- **Automated tests:** `tests/test_ideas.py`/`tests/test_org_write.py` — closing an idea as
  `DROPPED`/`RESEARCHED` results in it living in the archive file afterward; promoting to
  `PROMOTED` does the same; a non-terminal transition (`INCUBATE`) leaves the idea in place.
  `tests/test_export.py`/`tests/test_fit_log.py` — `pull_status` on a fixture EXPORTED idea
  whose portable status is `done` archives the linked idea; a second `pull_status` call is a
  no-op (idea stays archived, no error, no duplicate move); a fixture with no resolvable linked
  idea still returns a normal `pull_status` result (warning printed, not raised).
- **Manual verification:** close a real scratch idea as dropped and confirm it lands in the
  archive file; export→mark portable done→pull-status a real scratch outbound spec and confirm
  the same.
- **Regression guard:** full `uv run pytest` green; `set_state`/`pull_status` behavior for
  every non-triggering transition is unchanged.

## Rollout / migration

1. Depends on SPEC-0072 (`archive_idea` must exist).
2. Add both hooks; no data migration — existing already-terminal ideas in the real `ideas.org`
   are *not* retroactively archived by this spec (that would be a large, unreviewed bulk
   mutation of real data) — only newly-occurring transitions after this lands are archived
   automatically. A manual one-time backfill (mirroring SPEC-0064's outbound backfill) is a
   plausible separate follow-up, not part of this spec.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- None blocking.
