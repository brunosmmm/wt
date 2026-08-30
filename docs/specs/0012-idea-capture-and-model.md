---
id: SPEC-0012
title: Idea capture & model
status: done
owner: user
created: 2026-07-16
updated: 2026-07-17
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [ideas, org]
parent: SPEC-0011
depends_on: [SPEC-0005, SPEC-0010]
---

## Context

Foundation of the [SPEC-0011](./0011-idea-to-spec-pipeline.md) epic: make **ideas** a
first-class, lifecycle-bearing thing in org, reusing the existing parser / capture / write-back
pipeline. Today `~/work/org/ai/ideas.org` holds keyword-less idea headlines with freeform
incubation notes and no trackable state.

## Goals / Non-goals

**Goals**
- Config `org_ideas_file` + `org_idea_keywords`; the ideas file declares that `#+TODO` set.
- `Task.is_idea` (derived from the idea vocabulary) so ideas stay out of `wt tasks` by default.
- `wt idea "<text>"` to capture and `wt ideas` to list/filter ideas by state.

**Non-goals**
- Promotion to specs (SPEC-0013) or task generation (SPEC-0014).
- A separate Idea dataclass — ideas are `Task`s with `is_idea = True`.

## Decision

Ideas are org headlines whose TODO keyword is in the **idea vocabulary**
(`org_idea_keywords`, default `["IDEA", "INCUBATE", "SPECCED", "|", "PROMOTED", "DROPPED"]`),
living in `org_ideas_file` (default `~/work/org/ai/ideas.org`). `Task` gains a computed
`is_idea`. `wt idea` is a thin wrapper over `org_write.add_task` targeting the ideas file with
`IDEA` as the default state; `wt ideas` reuses `report`-style rendering, defaulting to the
open (non-done) idea states.

## Design

### Config (`src/wt/config.py`)

- `"org_ideas_file": "~/work/org/ai/ideas.org"`.
- `"org_idea_keywords": ["IDEA", "INCUBATE", "SPECCED", "|", "PROMOTED", "DROPPED"]`.

### Model (`src/wt/org.py`)

- Add `is_idea: bool = False` to `Task`, set in `_node_to_task` when `state` is in the idea
  vocabulary (`_split_keywords(cfg["org_idea_keywords"])`, both active + done sides). `load_tasks`
  passes the idea keyword set down. (A task's `is_done` still resolves against its own file's
  `#+TODO`, so `PROMOTED`/`DROPPED` read as done — an idea is "closed" when promoted or dropped.)
- `filter_tasks` gains `is_idea=None` to select/exclude ideas.
- **`wt tasks` stays task-only:** its actionable default already excludes non-active states, and
  it additionally filters `is_idea=False` so ideas never appear there.

### Capture (`src/wt/org_write.py`)

- `add_idea(cfg, text, *, state=None, tags=(), ...)` → `add_task(cfg, text, state=state or
  "IDEA", file=cfg["org_ideas_file"], ...)`. If the ideas file is new, it is created **with**
  the `#+TODO: <org_idea_keywords>` header so the states resolve.

### CLI (`src/wt/cli.py`)

```
wt idea Investigate self-assessing AI usage        # capture (default state IDEA)
wt idea "instant review agent" --state INCUBATE
wt ideas                                            # open ideas
wt ideas --all                                      # incl. PROMOTED/DROPPED
wt ideas --state INCUBATE
```

`report.ideas(cfg, *, state, all_done)` renders a table (state, idea, tags, linked-spec) via
`filter_tasks(..., is_idea=True)`. The `:SPEC:` property column is populated by SPEC-0013.

## Alternatives considered

- **`:kind:` property instead of a keyword set** — rejected (user decision); the keyword set
  reuses state/lifecycle machinery and keeps ideas non-actionable for free.
- **Separate Idea model** — rejected; a derived flag on `Task` avoids duplicating the parser.

## Acceptance criteria

- [x] `DEFAULT_CONFIG` has `org_ideas_file` + `org_idea_keywords`.
- [x] `Task.is_idea` is true iff `state` is in the idea vocabulary; `wt tasks` never shows ideas.
- [x] `wt idea "<text>"` appends an `* IDEA <text>` headline to the ideas file (creating it with
      the idea `#+TODO` header if missing); the idea is visible to `wt ideas`.
- [x] `wt ideas` lists open ideas by default; `--all` includes PROMOTED/DROPPED; `--state`
      filters.

## Test plan

- **Automated:** `tests/test_ideas.py` (tmp org dir): `add_idea` creates the ideas file with the
  idea `#+TODO`, and the captured task has `is_idea=True`, `state="IDEA"`; `wt tasks` excludes
  it; `wt ideas` includes it and honors `--state`/`--all`; `filter_tasks(is_idea=...)` selects
  correctly. CLI via `CliRunner`.
- **Manual verification:** `wt idea "…"` against a copy of real `ai/ideas.org`; `wt ideas`.
- **Regression guard:** `uv run pytest` stays green; `wt tasks` output unchanged for non-idea
  files.

## Rollout / migration

1. Config defaults. 2. `Task.is_idea` + `filter_tasks`/`report.tasks` idea exclusion.
3. `add_idea` + `report.ideas`. 4. `wt idea`/`wt ideas` CLI. 5. Tests + manual; close the loop.

## What shipped

Implemented as designed, no deviations. `DEFAULT_CONFIG` gained `org_ideas_file` +
`org_idea_keywords`; `Task.is_idea` (new trailing field, computed in `_node_to_task` from a
global idea-keyword set built by `load_tasks`, independent of each file's own `#+TODO`);
`filter_tasks(..., is_idea=None)`; `report.tasks` now filters `is_idea=False` in both its
default and `--all` branches so ideas never surface there. `org_write.add_idea` wraps
`add_task` against `org_ideas_file`, writing the `#+TODO: <org_idea_keywords>` header itself
before delegating when the file doesn't exist yet (so `add_task`'s own state validation sees
the idea vocabulary). `report.ideas` mirrors `report.tasks`'s rendering (state/idea/tags/spec
columns; the `spec` column reads a `:SPEC:` property, populated starting with SPEC-0013).
`wt idea`/`wt ideas` CLI commands added, following the `wt add`/`wt tasks` patterns.

One real-world note surfaced during manual verification: the live `~/work/org/ai/ideas.org`
predates this spec and has no `#+TODO` header (freeform keyword-less headlines), so
`add_idea` — which only injects the header for a **new** file — errors with "invalid state
'IDEA'" against it until that file gets the idea `#+TODO` header added once, by hand
(one line). This matches the Decision's file-creation scope and isn't a code change; it's a
one-time manual migration step for the existing file, called out here for whoever does the
rollout.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 80 passed; `tests/test_ideas.py`);
      manual verification performed (verifier: idea capture round-trip + `wt tasks` exclusion in a
      tmp workspace).
- [x] No regressions (pre-existing 66 tests still pass).
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
