---
id: SPEC-0064
title: "Frozen export-destination stamp + bulk pending-export reconciliation"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-077
kind: epic
milestone: "M4: cli ergonomics"
tags: [export, time-tracking, reliability]
---

## Context

Promoted from idea `IDEA-077` (Frozen export-destination stamp + bulk pending-export reconciliation sweep).

  :PROPERTIES:
  :ID: IDEA-077
  :END:
** Summary
Two gaps found while reviewing DEMO-0001's clocking flow:

1. Idea's :PROPERTIES: only stamp :PROJECT: and :SPEC: — the actual filesystem destination is **live-resolved** through config.yaml's outbox_targets[PROJECT].repo_path at read time, never frozen. If that config entry changes later, historical ideas silently point to the wrong place. The outbound spec's own frontmatter **does** freeze `target_repo`, but the idea itself does not.
2. `wt next` already reminds an EXPORTED/in-progress idea to run `wt spec pull-status`, but there is no equivalent reminder for `wt spec pull-clock` anywhere (next/hub/digest) — it only gets run if a human remembers.

Decision direction (not yet finalized): stamp the idea itself at export time with the precise destination — either one combined path property, or piecewise (`:TARGET_REPO:` + spec path/id), whichever is simpler to keep in sync on re-export. Then add a new command that scans all **pending** (non-terminal, not done/dropped/researched) exported ideas, visits each frozen target repo, and self-updates status + clock (i.e. runs the pull-status/pull-clock equivalent) in bulk, instead of requiring per-idea manual invocation.

**Resolved:** the sweep does NOT auto-run `fit-log` — fit/miss is a human judgment call about outcome, not a scrapable fact like status or clock time, so it stays a manual, separate action.
**Resolved:** if the frozen destination no longer exists on disk (repo moved/deleted) at sweep time, don't hard-error — record that fact durably in wt's own internal ledger so it's visible later (exact storage shape TBD during explore/spec).
** Open questions
*** RESOLVED Single frozen path property, or piecewise (repo + spec_dir/filename)?
*** OPEN Should this sweep also become the mechanism that fixes the missing pull-clock nudge in wt next, or are those two separate fixes?
*** OPEN Sweep reads: idea's mirrored :TARGET_REPO:/:TARGET_SPEC_PATH: properties directly, or always re-derive via :SPEC: -> outbound copy's frozen fields (idea properties as read-only display only)? Leaning toward the latter (single source of truth) but not decided.
** Log
*** [2026-07-26 Sun 12:51]
Traced actual path-resolution code (export.py). Outbound specs DO already freeze `target_repo` in their own frontmatter at scaffold time (specs.py ~L374), but this frozen value is **dead** — `_portable_dest_path()` (used by both `pull_status` and `pull_clock`) ignores it entirely and re-derives the destination fresh from **live** config every time: `target_project` (from outbound frontmatter) → `cfg['outbox_targets'][project]['repo_path']` + `spec_dir` (both from current config.yaml, not from anything frozen). So even outbound specs that already carry a `target_repo` field would silently resolve to a new path if `outbox_targets` config changes later — the freeze exists but isn't authxxitative for anything.

Revised direction: don't just add a property to the idea — fix path resolution itself to prefer a frozen, resolved value over live config, then mirror it. Concretely:
- At export/scaffold time, compute and freeze the **fully resolved absolute portable spec path** (not just the repo) into the outbound spec's own frontmatter (new field, e.g. `target_spec_path`), alongside the existing `target_repo`.
- Update `_portable_dest_path()` to prefer this frozen field when present, falling back to live `outbox_targets` config resolution only for specs that predate the field (backward compat).
- Mirror both `:TARGET_REPO:` and `:TARGET_SPEC_PATH:` (piecewise, matching the outbound spec's own shape — no new combined format to invent) onto the idea's org `:PROPERTIES:` drawer at the same moment `:SPEC:` is set, so a human can see the destination directly on the idea without opening the outbox copy.
- This answers open question 1 in favor of piecewise (repo + resolved spec path), matching the existing outbound-frontmatter shape rather than inventing a new combined format.

Not yet resolved: whether the new sweep command reads the idea's mirrored properties directly, or always goes idea → :SPEC: → outbound copy → frozen fields (idea properties would just be a display convenience in that case, not a second source of truth to keep in sync). Leaning toward the latter (single source of truth on the outbound copy; idea mirror is read-only display) to avoid a second place that can drift — but this needs to be nailed down in the spec.

## Goals / Non-goals

**Goals**
- Freeze the actual resolved export destination (target repo + absolute portable spec path) at
  export/scaffold time on the outbound spec's own frontmatter, and make path resolution
  actually use it instead of silently re-deriving from live config on every call.
- Mirror the frozen destination onto the source idea's org `:PROPERTIES:` drawer
  (`:TARGET_REPO:` / `:TARGET_SPEC_PATH:`) as a read-only display convenience.
- Add a bulk sweep command that scans every **pending** (non-terminal) EXPORTED idea, visits
  each frozen destination, and self-updates status + clock in one pass — reusing the existing
  `pull_status`/`pull_clock` functions rather than requiring per-idea manual invocation.
- If a frozen destination no longer exists on disk, record that fact durably (append to the
  same per-project `PROVENANCE.md` already used for export records) instead of hard-erroring
  and aborting the rest of the sweep.
- Give `wt next` a `pull-clock` hint alongside its existing `pull-status` hint for an
  EXPORTED/in-progress idea.

**Non-goals**
- No change to `fit-log` — stays a manual, human-judgment action; never auto-invoked by the
  sweep (resolved during explore: fit/miss is not a scrapable fact like status or clock time).
- No retroactive backfill requirement for outbound specs exported before this lands — they keep
  resolving via today's live-config derivation (backward-compatible fallback). A one-time
  backfill command is a plausible future add-on, explicitly out of scope here.
- Not a scheduled/background sync daemon — the sweep is an explicit, manually invoked command,
  matching `pull-status`/`pull-clock`'s existing on-demand shape.

## Decision

Freeze the resolved destination once, at the point it's currently computed live, instead of
re-deriving it from `outbox_targets` config on every `pull-status`/`pull-clock`/sweep call.
Make `_portable_dest_path()` prefer the frozen value when present, falling back to today's live
resolution only for specs that predate the new field. Mirror the same two fields onto the
source idea for human visibility. Add one new CLI command that iterates every EXPORTED,
non-terminal idea and calls the existing `pull_status`/`pull_clock` logic per idea — bulk
instead of one at a time — logging (not raising on) a missing destination.

## Architecture / cross-cutting design

- **New outbound-spec frontmatter field:** `target_spec_path` (absolute path string), computed
  and frozen once at scaffold time in `specs.py` (alongside the existing `target_repo` write,
  ~L374), using the same logic `_portable_dest_path()` uses today (`repo_path` + `spec_dir` +
  filename) — just computed once and stored, not recomputed on every read.
- **`_portable_dest_path(cfg, source_path, fm, to=None)`** (`export.py`): check
  `fm.get("target_spec_path")` first; an explicit `to=` override still wins (unchanged); only
  fall back to the current `outbox_targets`-based derivation when the frozen field is absent
  (pre-existing outbound specs).
- **Idea mirror:** at the same call site that sets `:SPEC:` (`specs.py` ~L388,
  `W.set_property(cfg, task, "SPEC", outbound_id)`), also mirror `:TARGET_REPO:` and
  `:TARGET_SPEC_PATH:` read back from the just-written outbound frontmatter.
  **Resolved (was open question):** these idea properties are read-only display only — the
  sweep and all path resolution always re-derive via `:SPEC:` → outbound copy's frozen fields.
  Single source of truth stays on the outbound copy; the idea mirror is never consulted
  programmatically, avoiding a second place that can drift.
- **New CLI (`wt spec sweep`, name confirmed in child C):** enumerate ideas with state
  `EXPORTED` that aren't terminal (excludes `done`/`DROPPED`/`RESEARCHED`); for each, resolve
  the outbound id via `:SPEC:` and call the existing `pull_status`/`pull_clock` functions
  (reuse, not reimplement). On a missing/unreadable destination, append a line to that
  project's `PROVENANCE.md` (matching the existing append-only precedent — no new storage
  format) and continue the sweep rather than aborting.
- **`wt next` hint (child D):** independent of the above — add a `pull-clock` companion to the
  existing `pull-status` hint in `next_step_for_idea` (`workflow.py`), same trigger condition
  (EXPORTED + status in-progress).

## Breakdown / sub-specs

- [x] SPEC-0065 — Freeze `target_spec_path` on outbound specs; `_portable_dest_path` prefers it
      with a backward-compatible fallback. — **done**
- [x] SPEC-0066 — Mirror `:TARGET_REPO:`/`:TARGET_SPEC_PATH:` onto the source idea at
      export/scaffold time (depends_on SPEC-0065 for the field it mirrors). — **done**
- [x] SPEC-0067 — `wt spec sweep`: bulk pull-status/pull-clock across pending exported ideas +
      missing-destination provenance logging (depends_on SPEC-0065). — **done**
- [x] SPEC-0068 — `wt next` pull-clock hint, parity with the existing pull-status hint
      (independent; can land in any order). — **done**

Sequencing / dependencies: SPEC-0065 lands first — nothing else works without the frozen field
existing. SPEC-0066 and SPEC-0068 can land in parallel with or after SPEC-0065. SPEC-0067
depends only on SPEC-0065, independent of SPEC-0066/SPEC-0068.

## Acceptance criteria

- [x] A freshly scaffolded/exported outbound spec has `target_spec_path` frozen in its
      frontmatter, reflecting the resolved absolute portable path at that moment.
- [x] Changing `outbox_targets[project].repo_path` in config after export does not change where
      `pull-status`/`pull-clock`/sweep look for an already-exported spec's portable copy.
- [x] The source idea's org node carries `:TARGET_REPO:` and `:TARGET_SPEC_PATH:` once its spec
      exports.
- [x] `wt spec sweep` reconciles status + clock across every pending EXPORTED idea in one run;
      a spec whose destination no longer exists on disk is recorded in that project's
      `PROVENANCE.md` rather than aborting the run.
- [x] `wt next` for an EXPORTED/in-progress idea surfaces a pull-clock hint in addition to the
      existing pull-status hint.

## Test plan

- **Integration/e2e tests:** export a fixture idea, assert `target_spec_path` is frozen in
  frontmatter; mutate `outbox_targets` config afterward and assert `pull-status`/`pull-clock`/
  sweep still resolve the original frozen path, not the mutated one; assert the source idea's
  org node gains the mirrored properties; run the sweep across multiple fixture EXPORTED ideas
  (one with a valid destination, one with its destination deleted) and assert partial success
  plus a provenance record for the missing one; assert the new `wt next` hint text appears for
  an EXPORTED/in-progress fixture idea. Per-unit coverage of each piece lives in its child spec.
- **Manual verification:** run the full export → mutate-config → sweep loop against a real
  scratch idea/outbound pair; eyeball `wt idea show` for the mirrored properties.
- **Regression guard:** full `uv run pytest` green; pre-existing outbound specs without
  `target_spec_path` keep resolving via the unchanged live-config fallback.

## Rollout / sequencing

1. SPEC-0065 (frozen field + resolution fix) lands first — usable immediately, fixes the
   silent-drift bug on its own even before the sweep exists.
2. SPEC-0066 (idea mirror) and SPEC-0068 (`wt next` hint) land next, independent of each other.
3. SPEC-0067 (`wt spec sweep`) lands last, once SPEC-0065's frozen field is stable to sweep
   against.

## Definition of done

- [x] All child specs `done` or `superseded` (the linter gates this).
- [x] Integration test plan executed; `uv run pytest` green.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

- None blocking — both questions raised during explore were resolved during authxxing: path
  format is piecewise (`target_repo` + `target_spec_path`, matching the existing outbound
  frontmatter shape rather than inventing a new combined format), and the idea's mirrored
  properties are read-only display only (single source of truth stays on the outbound copy).
