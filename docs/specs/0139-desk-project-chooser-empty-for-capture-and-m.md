---
id: SPEC-0139
title: "Desk project chooser uses projects_payload names (capture + m→project)"
status: done
owner: user
created: 2026-09-01
updated: 2026-09-01
milestone: "M5: interactive desk"
kind: feature
tags: [tui, bug, project]
depends_on: [SPEC-0109, SPEC-0095]
source_idea: IDEA-340
---

## Context

[SPEC-0109](./0109-found-another-shortcoming-when-capturing-ideas.md) shipped desk project
assign on capture (`c`) and metadata (`m` → project), with `(none)` to clear. Both surfaces
build the chooser from `known_project_choices` → `known_projects()` (mappings.yaml buckets
only, [SPEC-0018](./0018-capture-entity-association.md)).

Later, [SPEC-0095](./0095-wt-projects-json-and-multi-project-gate.md) /
[SPEC-0137](./0137-wt-projects-add-cli-register-outbox-targets-dry.md) made
`projects_payload` / `wt projects --json` the live project map: mappings ∪ `outbox_targets`
∪ `Meta-Tools`. The desk never adopted that union.

**Symptom (IDEA-340, 2026-09-01):** with no `mappings.yaml`, `known_projects` is `[]`.
Capture silently skips the project step (`len(choices)==1`). `m` → project opens a chooser
with only `(none)` — looks empty; cannot assign DemoBrew or Meta-Tools even though
`wt projects` lists them. SPEC-0109's claim that free-text "remains reachable" is false on
the desk (only `ChoiceScreen`; CLI `--set` is the escape hatch).

## Goals / Non-goals

**Goals**

- Desk capture and `m` → project offer the same project names `wt projects` knows.
- `(none)` still clears; capture may still decline a project.
- Empty-after-union is honest UX (notify), not a silent skip or a clear-only chooser.
- One write path unchanged: desk still goes through `apply_mutation` / `capture_idea`.

**Non-goals**

- Changing `known_projects()` itself (CLI completion / unknown-association warnings stay
  mappings-derived for this spec; optional follow-up).
- Free-text project entry on the desk (deferred; union fix is enough when Meta-Tools /
  outbox exist).
- Closed vocabulary, richer capture (kind/priority in the same flow), research-context
  changes, retro-assigning existing project-less ideas.

## Decision

`known_project_choices(cfg)` returns the sorted project **names** from
`projects_payload(cfg)` (same union as `wt projects --json`), not `known_projects(cfg)`
alone.

Capture and `m` → project keep using that helper. If the resulting list is empty: **notify**
and do **not** open a chooser that is only `(none)`; capture writes with no project;
`m` → project aborts without a modal. When the list is non-empty, behaviour matches
SPEC-0109 (offer `(none)` + names; `--project` filter pre-selects on capture).

This amends SPEC-0109's desk wiring only; it does not reopen SPEC-0018's definition of
`known_projects`.

## Design

**Library (`src/wt/tui/model.py`).** `known_project_choices`:

```python
def known_project_choices(cfg) -> list[str]:
    from ..rules import projects_payload
    try:
        return [p["name"] for p in projects_payload(cfg)["projects"]]
    except (OSError, ValueError, KeyError, TypeError):
        return []
```

`projects_payload` already sorts names and always includes `Meta-Tools`, so a normal
install never yields `[]` after this change.

**Desk (`src/wt/tui/app.py`).**

- Capture: `choices = [NONE_CHOICE] + known_project_choices(cfg)`. If
  `known_project_choices` is empty → `notify` (e.g. "no projects configured") and
  `write(text, None)` — same end state as today's skip, but visible.
- `m` → project: if choices empty → `notify` and return (do not push `ChoiceScreen` with
  only `(none)`). Otherwise `[(none)] + names` as today.

**Tests.** Extend `tests/test_idea_project.py` (and/or desk pilot):

- Config with **no** mappings but `outbox_targets: {DemoBrew: {repo_path: …}}` → choices
  include `DemoBrew` and `Meta-Tools`.
- Existing mappings-seeded test still passes (union ⊇ mapping buckets).
- Degrade path (no `config_dir`) still returns `[]` without raising.

## Alternatives considered

- **Widen `known_projects()` to the same union** — rejected for this slice: broader blast
  radius on CLI warnings/completion; desk-only helper is enough to fix the reported bug.
- **Free-text Input when empty** — deferred: after the union, empty is pathological; notify
  is enough. Free-text remains a possible follow-up idea.
- **Hand-edit mappings.yaml as the workaround** — rejected as the product fix; operators
  should not need fake mapping buckets to pick DemoBrew on the desk.
- **Supersede all of SPEC-0109** — unnecessary; only the chooser source is wrong.

## Acceptance criteria

- [x] With no mappings file and at least one `outbox_targets` key, desk capture offers that
      key and `Meta-Tools` in the project chooser (plus `(none)`).
- [x] Under the same config, `m` → project offers those names (plus `(none)`), not only
      `(none)`.
- [x] Choosing a name writes `:PROJECT:` (capture and metadata); `(none)` clears.
- [x] When `known_project_choices` is empty, capture notifies and does not pretend a
      chooser; `m` → project notifies and does not open a clear-only modal.
- [x] `known_projects()` behaviour for CLI warn/complete is unchanged by this spec.
- [x] Automated tests cover outbox-only (no mappings) choices; existing project-desk tests
      stay green.

## Test plan

- **Automated:** `tests/test_idea_project.py` — add
  `test_known_project_choices_includes_outbox_and_meta_tools_without_mappings`; keep
  degrade-to-`[]` and mappings-seeded cases. Optional Textual pilot: capture shows DemoBrew
  when only outbox is configured.
- **Manual:** `wt tui` on a config with empty/missing mappings and `outbox_targets.DemoBrew`;
  `c` → text → project list includes DemoBrew + Meta-Tools; `m` → project same; assign and
  clear round-trip (`wt idea show`).
- **Regression:** `uv run pytest tests/test_idea_project.py tests/test_assoc.py` — mappings
  `known_projects` tests unchanged.

## Rollout / migration

Ship with the next Meta-Tools build. No data migration. Operators with empty mappings get
working desk project assign immediately; no config rewrite required.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — decided in Decision: desk `known_project_choices` ← `projects_payload` names;
empty → notify; do not widen `known_projects` in this spec.
