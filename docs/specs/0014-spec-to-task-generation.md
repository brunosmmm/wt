---
id: SPEC-0014
title: Spec → org task/epic generation
status: done
owner: user
created: 2026-07-16
updated: 2026-07-17
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [specs, org, tasks]
parent: SPEC-0011
depends_on: [SPEC-0012, SPEC-0013]
---

## Context

Closes the internal funnel of the [SPEC-0011](./0011-idea-to-spec-pipeline.md) epic: turn an
accepted spec into **org tasks** so the work is trackable, and its tracked time joins back in
`wt digest`. A spec's *Breakdown / sub-specs* (epic) or *Acceptance criteria* (feature) is the
natural task source.

## Goals / Non-goals

**Goals**
- `wt spec generate <spec-id>` emits org tasks from a spec into the capture/agenda file, one per
  breakdown item (epic) or a single tracking task (feature), keyed to the spec so time joins.
- Idempotence: re-running doesn't duplicate tasks (match on a `:SPEC:` property carried on each
  generated task).
- Advance the source idea `SPECCED → PROMOTED` when its spec has generated tasks.

**Non-goals**
- Two-way sync of task state back into the spec (a spec's status is authxxed, not derived).
- Outbound/other-repo specs (SPEC-0015) — this generates local org tasks for `wt`'s own join.

## Decision

Add `wt spec generate <spec-id> [--file F]`. Parse the spec (reuse `spec_lint.split_frontmatter`
/ `sections`), extract breakdown/AC items, and `org_write.add_task` each as a `TODO` under a
generated parent heading named for the spec, tagging every task with a `:SPEC:<id>:` property so
re-runs are idempotent and the join key is explicit. If the spec has a `source_idea`, advance
that idea to `PROMOTED`.

## Design

### Extraction (`src/wt/specs.py`)

- `spec_tasks(spec) -> (title, [item, ...])`: for `kind: epic`, items = the `- [ ] SPEC-…` /
  bullet lines under **Breakdown / sub-specs**; for a feature, items = the **Acceptance
  criteria** bullets (or a single "implement <title>" task if none). Strip checkbox/markup.
- The join key: prefer the spec's own JIRA key if its title/id encodes one; else the tasks carry
  `:SPEC:<spec-id>:` and (optionally) a `--key DEMO-NNN` to set `topic_key` for the time join.

### Generation (`src/wt/org_write.py`)

- `generate_tasks(cfg, spec, items, *, file=None, key=None)`:
  - Target = `file or cfg["org_capture_file"]`.
  - Ensure a parent heading `* <spec-id> <title>  :spec:` exists (create once; idempotent by
    scanning for a heading carrying `:SPEC:<id>:`).
  - For each item not already present (match on text under that parent), `add_task` a `TODO`
    child with a `:SPEC:<id>:` property (and `:TOPIC:<key>:` when `--key` given, so
    `topic_key` drives the `wt digest` join).
- Reuses backup + atomic write; never edits unrelated headings.

### CLI (`src/wt/cli.py`)

```
wt spec generate SPEC-0011                         # tasks from the epic's breakdown
wt spec generate SPEC-0020 --key DEMO-100          # feature spec, tasks keyed to a JIRA id
wt spec generate SPEC-0011 --file ~/work/org/agenda.org
```

## Alternatives considered

- **Generate into a brand-new file per spec** — rejected; cluttered. A per-spec parent heading in
  an existing file groups them and keeps `Task.project` meaningful.
- **Derive spec status from task completion** — rejected; specs are authxxed artifacts, and
  conflating the two breaks the governance timeline.
- **No idempotence** — rejected; re-generation is common as a spec's breakdown evolves.

## Acceptance criteria

- [x] `wt spec generate <epic-id>` creates one parent heading + a `TODO` per breakdown item,
      each carrying a `:SPEC:<id>:` property; re-running adds only new items (no duplicates).
- [x] A feature spec generates a tracking task (from ACs or a single task).
- [x] `--key` sets each task's `topic_key` so its tracked time joins in `wt digest` (verified via
      the join invariant on a synthetic tracked topic).
- [x] A spec with `source_idea` advances that idea to `PROMOTED`.

## Test plan

- **Automated:** `tests/test_generate.py` (tmp org + a fixture spec): generate tasks; assert the
  parent + children exist with `:SPEC:` props, re-run is idempotent, `--key` yields matching
  `topic_key` and `org.join_time` attributes a synthetic topic's seconds to a generated task
  (the join invariant), and the linked idea moves to `PROMOTED`. CLI via `CliRunner`.
- **Manual verification:** `wt spec generate` a real spec into a temp org file; `wt tasks` +
  `wt digest` show the generated tasks.
- **Regression guard:** `uv run pytest` green; `add_task`/read path unaffected.

## Rollout / migration

1. `spec_tasks` extraction. 2. `generate_tasks` (idempotent, keyed). 3. `wt spec generate` CLI.
4. Tests (incl. join invariant) + manual; close the loop.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 101 passed; `tests/test_generate.py`);
      manual verification by the verifier (independent temp-dir generate: 4 children, idempotent
      re-run, all keyed, join invariant 3600s→key with no untracked).
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._

## What shipped / deviations

Implemented as designed, no material deviations:

- `specs.spec_tasks(spec_path)` reuses `tools/spec_lint.split_frontmatter`/`sections` (loaded
  dynamically via `importlib`, since `tools/` is a dev script dir, not an installed package) to
  extract `(title, items)` — breakdown lines for `kind: epic`, Acceptance-criteria bullets (or a
  single `"implement <title>"`) for a feature.
- `org_write.generate_tasks(cfg, spec, items, *, file=None, key=None)` locates an existing
  parent via `load_tasks` (a level-1 heading whose `:SPEC:` property matches), or appends a new
  one (`* <id> <title>  :spec:`), then appends only the not-yet-present children (level-2 `TODO`s
  with `:SPEC:`/optional `:TOPIC:` properties) directly under the parent's subtree — computed by
  scanning raw lines from the parent's headline to the next heading at or above its level.
- `specs.generate_from_spec(cfg, spec_id, *, file=None, key=None)` ties `spec_tasks` +
  `generate_tasks` together and advances a `source_idea` to `PROMOTED` via `set_state`.
- CLI: `wt spec generate <spec-id> [--file F] [--key DEMO-NNN]`, added to the existing `spec`
  group.
- Verified: `tests/test_generate.py` (10 tests — extraction, idempotence w/ a growing breakdown,
  the join invariant via `org.join_time`, `source_idea` → `PROMOTED`, custom `--file` target,
  CLI). Manual: ran `generate_from_spec` against the real `docs/specs/0011-*.md` (copied into a
  tmp `specs_dir`) into a tmp org file — produced the parent heading + 6 children keyed
  `DEMO-100`; `join_time(tasks, {"DEMO-100": 5400.0})` attributed the full 5400s to that key with
  no `untracked` entries; a second run added 0 new tasks.
