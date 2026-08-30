---
id: SPEC-0066
title: "Mirror :TARGET_REPO:/:TARGET_SPEC_PATH: onto the source idea at scaffold time"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-079
parent: SPEC-0064
milestone: "M4: cli ergonomics"
tags: [export, time-tracking]
depends_on: [SPEC-0065]
---

## Context

Promoted from idea `IDEA-079` (SPEC-0066).

  :PROPERTIES:
  :ID: IDEA-079
  :EPIC: SPEC-0064
  :END:
** Summary
Child of epic `SPEC-0064`.

SPEC-0066 — Mirror `:TARGET_REPO:`/`:TARGET_SPEC_PATH:` onto the source idea at
** Open questions

** Log

## Goals / Non-goals

**Goals**
- At the moment an outbound spec's `:SPEC:` property is written onto its source idea, also
  mirror `:TARGET_REPO:` and `:TARGET_SPEC_PATH:` onto the same idea, read back from the
  outbound frontmatter that SPEC-0065 just froze.
- Make the export destination visible directly on `wt idea show <id>` without requiring anyone
  to separately open the outbox copy.

**Non-goals**
- Not a second source of truth: nothing (sweep, pull-status, pull-clock) ever reads these
  mirrored properties programmatically — they're display-only. All path resolution stays on
  the outbound copy's frontmatter (SPEC-0065). This was an explicit resolution during explore,
  to avoid a second place that can drift out of sync.
- Not updating the mirror on every `pull-status`/`pull-clock` call — it's written once, at the
  same scaffold moment `:SPEC:` is set. If the destination ever changes (re-export to a new
  target), that's out of scope here (see Open questions).

## Decision

Mirror the two fields at the exact same call site that already writes `:SPEC:` onto the idea
(`specs.py::scaffold_outbound`), reading them from the outbound frontmatter text already
written a few lines earlier in the same function — no new lookup needed, just two more
`W.set_property` calls beside the existing one.

## Design

- **`specs.py::scaffold_outbound()`, ~L388-390:** immediately beside the existing
  `W.set_property(cfg, task, "SPEC", outbound_id)` call, add:
  ```python
  W.set_property(cfg, task, "TARGET_REPO", target_repo)
  W.set_property(cfg, task, "TARGET_SPEC_PATH", target_spec_path)
  ```
  Both `target_repo` and `target_spec_path` are already local variables in this function by the
  time this line runs (the latter added by SPEC-0065) — no re-read of the just-written outbound
  file needed.
- **`org_write.py::set_property()`** (existing, unchanged) already handles drawer creation and
  drift-guarding; called exactly like the existing `SPEC` property write, same conventions.
- No change to `wt idea show` rendering — it already prints the full `:PROPERTIES:` drawer, so
  the new properties appear automatically once written.

## Alternatives considered

- **Store one combined path string instead of two properties** — rejected: mirrors SPEC-0065's
  own frontmatter shape (`target_repo` + `target_spec_path` as separate fields); inventing a
  different combined format on the idea side than what the outbound copy uses adds a second
  format to remember for no benefit.
- **Have the sweep (SPEC-0067) read these mirrored properties instead of the outbound copy** —
  rejected per SPEC-0064's Architecture decision: single source of truth stays on the outbound
  copy; these are read-only display.

## Acceptance criteria

- [x] After `wt spec new --target <project> --from-idea <id>` (or promoting an idea with a
      `:PROJECT:`), the source idea's org node carries `:TARGET_REPO:` and
      `:TARGET_SPEC_PATH:` properties matching the outbound spec's frontmatter.
- [x] `wt idea show <id>` displays both new properties as part of the existing properties
      output — no dedicated rendering code needed.
- [x] Re-running the sweep (SPEC-0067) or `pull-status`/`pull-clock` behavior is unaffected —
      these properties are never read by any resolution code path.

## Test plan

- **Automated tests:** `tests/test_specs.py` — scaffolding an outbound spec from an idea with
  `:PROJECT:` set results in `:TARGET_REPO:`/`:TARGET_SPEC_PATH:` on the idea's org node,
  matching the outbound file's own frontmatter values.
- **Manual verification:** scaffold a real scratch outbound spec from a scratch idea, run
  `wt idea show <id>`, confirm both properties render.
- **Regression guard:** full `uv run pytest` green; existing `:SPEC:`/`:PROJECT:` property
  behavior and `wt idea show` output for ideas without a linked outbound spec unchanged.

## Rollout / migration

1. Depends on SPEC-0065 landing first (needs `target_spec_path` to exist as a local variable
   at the write site).
2. Add the two `set_property` calls; no data migration — ideas exported before this lands
   simply don't have the mirrored properties (same non-goal as SPEC-0065's fallback).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- None blocking. (Re-export/re-target refreshing the mirror is out of scope — see Non-goals;
  revisit if re-targeting an already-exported idea turns out to be a real workflow.)
