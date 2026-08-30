---
id: SPEC-0018
title: Entity association on capture (project / epic / key)
status: done
owner: user
created: 2026-07-18
updated: 2026-07-18
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [cli, ideas, tasks, org]
depends_on: [SPEC-0010, SPEC-0012, SPEC-0013]
---

## Context

`wt idea` / `wt add` today capture only a bare headline (+ `--tag`/`--priority`). That's too
thin: when you capture a thought you usually already know **which project** it belongs to and
sometimes **which epic**, and you want the JIRA **key** pinned for the time-join. `wt` already
*has* these entities — it just doesn't let you attach them at capture:

- **Known projects** = the distinct values of the facet **bucket** axis in `mappings.yaml`
  (e.g. `Demo-ATS`, `DemoCloud`, `Logging`, `qcs8550-resources`). Base topics (repo/JIRA) are
  auto-detected during time tracking; the human-friendly *project* is the bucket you mapped via
  `wt map`. This is the de-facto project registry.
- **Known epics** = specs with `kind: epic` (`SPEC-0004`, `SPEC-0011`).

## Goals / Non-goals

**Goals**
- `--project <bucket>`, `--epic SPEC-NNNN`, and `--key DEMO-NNN` on **both** `wt idea` and
  `wt add`, stored as durable org properties the `Task` model reads back.
- Epic association **threads into promotion**: `wt spec new --from-idea` sets the scaffolded
  spec's `parent:` to the associated epic.
- `wt projects` lists the known buckets (so `--project` values are discoverable).
- **Permissive** validation: an unknown project/epic warns + lists the known set, but never
  blocks capture.

**Non-goals**
- A new project *registry* — the facet/bucket layer already is one.
- Changing the time-tracking → bucket facet mapping (`wt map`) itself.
- Auto-inferring project/epic from context (explicit flags only in v1).

## Decision

Add the three association flags to both capture verbs, stored as `:PROJECT:` / `:EPIC:` /
`:TOPIC:` properties on the created headline. The `Task` model gains `epic` and lets
`:PROJECT:` **override** its structural project (mirroring how `:TOPIC:` already overrides the
headline-derived key). Promotion honors `:EPIC:` as `parent:`. Validation is permissive: warn
and list the known set on an unknown value, then proceed.

## Design

### Config (`src/wt/config.py`)

- `"project_axis": "bucket"` — which facet axis is treated as "project" (the user uses
  `bucket`). Known projects = distinct values of this axis across `mappings.yaml`.

### Known-entity helpers

- `rules.known_projects(cfg) -> list[str]` — sorted distinct values of `cfg["project_axis"]`
  across `load_mappings(cfg)`.
- Known epics: reuse `specs`/`spec_lint` to list `kind: epic` spec ids under `cfg["specs_dir"]`
  (default `docs/specs`). A small `specs.known_epics(cfg) -> list[str]`.

### Model (`src/wt/org.py`)

- `Task` gains `epic: str | None = None` (from the `:EPIC:` property), trailing field.
- `project`: prefer the `:PROJECT:` property, else the existing nearest-level-1/file-stem
  derivation. (No regression: nothing has `:PROJECT:` today. `wt digest --by project` then
  groups associated captures under their bucket.)

### Capture (`src/wt/org_write.py`)

- `add_task(...)` / `add_idea(...)` gain `project=None, epic=None, key=None`. When any is set,
  the appended headline gets a `:PROPERTIES:` drawer with `:PROJECT:`/`:EPIC:`/`:TOPIC:`
  (reusing the property-drawer writing already used by `generate_tasks`).
- Validation (permissive): if `project` ∉ `known_projects`, print a warning + the known list;
  if `epic` isn't a known epic id, warn + list known epics; **proceed regardless**.

### Promotion threading (`src/wt/specs.py`)

- `scaffold_from_idea`: if the idea has an `:EPIC:` property that **resolves to a real
  `kind: epic` spec**, inject `parent: <epic>` into the scaffolded spec's frontmatter. If it
  doesn't resolve, warn and leave `parent` unset (so we never write a spec that fails
  `parent`-integrity lint). Permissive capture, safe promotion.

### CLI (`src/wt/cli.py`)

```
wt idea "adaptive logging" --project Logging --epic SPEC-0011 --key DEMO-817
wt add  "wire the dashboard" --project Demo-ATS --key DEMO-900
wt projects                      # list known buckets (+ topic counts)
```

`--project`/`--epic`/`--key` added to `idea_cmd` and `add_cmd`; new `wt projects`.

## Alternatives considered

- **Store project as a tag** — rejected; conflates with org tags and doesn't override
  `Task.project` for digest grouping. A property is cleaner and machine-readable.
- **Strict validation** — rejected (user decision); capture must stay frictionless. Permissive
  + suggestion catches typos without blocking.
- **A dedicated project registry file** — rejected; `mappings.yaml` buckets already are it.

## Acceptance criteria

- [x] `wt idea` and `wt add` accept `--project`, `--epic`, `--key`; the values land as
      `:PROJECT:`/`:EPIC:`/`:TOPIC:` properties and re-parse (`Task.project` = the property,
      `Task.epic` set, `Task.topic_key` = the key).
- [x] An unknown `--project`/`--epic` warns and lists the known set but still captures.
- [x] `wt spec new --from-idea` on an idea with a valid `:EPIC:` sets the scaffolded spec's
      `parent:`; an unresolvable epic warns and leaves `parent` unset (spec still lints).
- [x] `wt projects` lists the known buckets.
- [x] `wt digest --by project` groups an associated capture under its `--project` bucket.

## Test plan

- **Automated:** extend `tests/test_ideas.py`/`test_org_add.py` (or a new `tests/test_assoc.py`):
  capture with each flag → re-parse asserts properties + `Task.project`/`epic`/`topic_key`;
  unknown project/epic warns (captured via `CliRunner`/`capsys`) but writes; `known_projects`
  returns the mapping's buckets; promotion sets `parent:` for a valid epic and skips + warns for
  an invalid one (spec still passes `spec_lint.validate`); `wt projects` output. CLI via
  `CliRunner`.
- **Manual verification:** `wt idea "…" --project Logging --epic SPEC-0011 --key DEMO-817` in a
  temp workspace, then `wt ideas` + re-parse; `wt projects` against the real `mappings.yaml`.
- **Regression guard:** `uv run pytest` green; existing `wt add`/`wt idea`/digest unaffected when
  the new flags are omitted.

## Rollout / migration

1. `project_axis` config + `known_projects`/`known_epics` helpers.
2. `Task.epic` + `:PROJECT:` override in `org.py`.
3. `add_task`/`add_idea` property drawer + permissive validation.
4. `scaffold_from_idea` parent threading.
5. `--project`/`--epic`/`--key` on `wt idea`/`wt add` + `wt projects`.
6. Tests + manual; close the loop.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 181 passed; `tests/test_assoc.py`); manual verification by the verifier (all-flags capture re-parse, permissive warning, promotion parent-threading, `wt projects` on real mappings).
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._

## What shipped / deviations

Implemented as designed, no deviations:

- `config.DEFAULT_CONFIG["project_axis"] = "bucket"`.
- `rules.known_projects(cfg)` (sorted distinct `project_axis` values across `load_mappings`)
  and `specs.known_epics(cfg)` (sorted ids of `kind: epic` specs under `cfg["specs_dir"]`).
- `org.Task.epic` (new trailing field, from `:EPIC:`); `org._project` now prefers a `:PROJECT:`
  property over the structural derivation.
- `org_write.add_task`/`add_idea` gained `project=None, epic=None, key=None`, writing a
  `:PROPERTIES:` drawer (`:PROJECT:`/`:EPIC:`/`:TOPIC:`) on the appended headline, reusing the
  drawer-writing convention from `generate_tasks`. Validation is permissive
  (`_warn_unknown_associations`): an unknown project/epic prints a `! unknown project/epic ...`
  warning + the known set to stderr, then proceeds unconditionally.
- `specs.scaffold_from_idea` injects `parent: <epic>` when the idea's `:EPIC:` resolves to a
  known `kind: epic` spec; otherwise warns to stderr and leaves `parent` unset (verified the
  scaffolded spec still passes `spec_lint.validate` either way).
- CLI: `--project`/`--epic`/`--key` on `wt idea` and `wt add`; new `wt projects` (lists known
  buckets with a topic-count, or a friendly "no projects mapped yet" message).
- Tests: `tests/test_assoc.py` (16 cases) covering `known_projects`/`known_epics`, capture +
  re-parse of all three properties, `:PROJECT:` overriding structural project, the permissive
  unknown-project/epic warning paths, promotion parent-threading (valid + unresolvable epic,
  both lint-clean), `wt projects`/`wt idea`/`wt add` CLI, and `wt digest --by project` grouping
  a captured `--project` bucket. Full suite: `uv run pytest` → 181 passed. `python3
  tools/spec_lint.py` → exit 0. Manual verification performed in a temp workspace (tmp org/
  specs/config dirs): capture-with-all-three-flags re-parsed correctly, the permissive-warning
  path proceeded despite unknown values, and promotion set `parent: SPEC-0011` for a valid
  epic while leaving it unset (with a warning) for an unresolvable one.

**Follow-up (post-done):** SPEC-0018 stored and *used* the associations (digest grouping,
promotion) but the `wt ideas` listing didn't *display* them — it showed only state/idea/tags/
spec. Added a **project** column (the explicit `:PROJECT:`, not the file-stem-fallback
`Task.project`) plus a **refs** column (key / ⊂epic / →spec) to `report.ideas`, with a test.
(`wt tasks` already surfaces the project via its "project · tags" column.)
