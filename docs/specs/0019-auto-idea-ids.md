---
id: SPEC-0019
title: Auto-assigned stable idea IDs
status: done
owner: user
created: 2026-07-18
updated: 2026-07-18
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [cli, ideas, org]
depends_on: [SPEC-0009, SPEC-0012, SPEC-0018]
---

## Context

An idea has no stable short handle today. `Task.id` falls back to `file:line`, which **shifts**
as the ideas file is edited, so the only way to reference an idea for `wt spec new --from-idea`
is a heading substring — fragile once you have more than a handful. To work a backlog of ideas
("pick IDEA-7, flesh it out"), each needs a durable, memorable id.

## Goals / Non-goals

**Goals**
- `wt idea` auto-assigns a stable `:ID: IDEA-NNN` (sequential) at capture, printed on capture.
- `wt ideas` shows the id as the first column; `wt spec new --from-idea IDEA-NNN` resolves it.
- `wt ideas --reindex` backfills ids onto existing id-less ideas (idempotent, stable).

**Non-goals**
- IDs for tasks (`wt add`) — ideas only (user decision).
- Renumbering/compacting existing ids (once assigned, an id is permanent).
- A global id registry — ids live as `:ID:` org properties, scoped to the ideas file.

## Decision

At capture, `add_idea` writes `:ID: IDEA-{n:03d}` where `n` = next free number across ideas
(scan `:ID:` values matching `IDEA-(\d+)`, max+1, start 1). The id is the FIRST property in the
drawer. `Task.id` already prefers `:ID:`, and `resolve_selector` already matches `t.id`, so the
id is immediately usable as a selector (with light normalization so `idea-7` ≡ `IDEA-007`).
`wt ideas` gains an id column; `wt ideas --reindex` fills gaps for pre-existing ideas.

## Design

### Numbering (`src/wt/org_write.py`)

- `next_idea_number(cfg) -> int`: over `load_tasks(cfg)` filtered to `is_idea`, parse `:ID:`
  values matching `^IDEA-(\d+)$`; return `max(...) + 1` (or 1). Zero-pad to 3 in the id string
  (`IDEA-001`); numbers ≥ 1000 just render wider.

### Capture (`src/wt/org_write.py`)

- `add_idea(...)` assigns `id = f"IDEA-{next_idea_number(cfg):03d}"` and writes `:ID:` as the
  first line of the `:PROPERTIES:` drawer (before `:PROJECT:`/`:EPIC:`/`:TOPIC:`). Returns the
  id alongside `(path, headline)` so the CLI can echo it.

### Selector normalization (`src/wt/org_write.py:resolve_selector`)

- Before the existing exact-match passes, normalize an `IDEA-<n>` selector: uppercase and
  zero-pad the numeric part, so `idea-7`/`IDEA-7` match the stored `IDEA-007`. Other selector
  forms (topic_key, heading substring) unchanged.

### Reindex (`src/wt/org_write.py`, `wt ideas --reindex`)

- `reindex_ideas(cfg) -> list[(id, heading)]`: for each idea lacking a valid `IDEA-NNN` `:ID:`,
  in file order, assign the next number via `set_property` (reusing backup + atomic write).
  Idempotent: ideas that already have an id keep it. Returns what it assigned.

### CLI (`src/wt/cli.py`)

- `wt idea …` prints the assigned id: `✓ IDEA-007  <headline>  <path>`.
- `wt ideas` gains a leading **id** column (`tk.properties.get("ID","")`).
- `wt ideas --reindex` backfills, prints the assignments, then lists.

## Alternatives considered

- **Short random slug (`idea-7f3a`)** — rejected (user decision); not memorable/sortable.
- **`file:line` as the handle** — the status quo; rejected because it shifts on edit.
- **Auto-backfill on `wt ideas` (a read command)** — rejected; a listing must not mutate files.
  Backfill is an explicit `--reindex`.

## Acceptance criteria

- [x] `wt idea "<text>"` writes `:ID: IDEA-NNN` (sequential, unique), prints it, and it shows in
      `wt ideas`' id column.
- [x] `wt spec new --from-idea IDEA-NNN` resolves the idea (and `idea-n` normalizes to it).
- [x] `wt ideas --reindex` assigns ids to id-less ideas in file order, leaves existing ids
      untouched, and is idempotent (a second run assigns nothing).
- [x] Numbering never collides with an existing `IDEA-NNN`.

## Test plan

- **Automated:** extend `tests/test_ideas.py`/`test_assoc.py`: capture → `:ID:` present +
  sequential across multiple captures; `Task.id == "IDEA-001"`; `resolve_selector` matches
  `IDEA-001` and `idea-1`; `next_idea_number` respects existing ids (no collision after a gap);
  `reindex_ideas` backfills only id-less ideas and is idempotent; `wt ideas` shows the id column;
  CLI echoes the id. Via `CliRunner` + tmp org.
- **Manual verification:** `wt idea "x"` in a temp workspace → note the id; `wt ideas`;
  `wt spec new --from-idea IDEA-001` (tmp specs dir) resolves it; `wt ideas --reindex` on a file
  with a pre-existing id-less idea.
- **Regression guard:** `uv run pytest` green; existing capture/promotion/selector tests pass.

## Rollout / migration

1. `next_idea_number` + `add_idea` id assignment (returns id).
2. `resolve_selector` normalization.
3. `reindex_ideas` + `wt ideas --reindex`; id column in `wt ideas`; `wt idea` echo.
4. Tests + manual; close the loop. (Your one existing id-less idea gets an id via `--reindex`.)

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 190 passed); manual verification by the verifier (sequential IDs, `idea-2`→IDEA-002 resolve, gap-safe + idempotent reindex).
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._

## What shipped / deviations

Implemented exactly as designed, no deviations:

- `next_idea_number(cfg)` and `reindex_ideas(cfg)` added to `src/wt/org_write.py`.
- `add_task` gained an `idea_id` kwarg (writes `:ID:` first in the drawer); `add_idea` assigns
  `IDEA-{n:03d}` via `next_idea_number` and now returns `(path, headline, id)`.
- `resolve_selector` normalizes an `IDEA-<n>` selector (any case/padding) to `IDEA-NNN` before
  matching, so `idea-1`/`IDEA-1` resolve `IDEA-001`.
- `wt idea` echoes the assigned id (`✓ IDEA-NNN  <headline>  <path>`); `wt ideas` gained a
  leading id column; `wt ideas --reindex` backfills id-less ideas (re-parsing after each
  assignment since inserting a drawer shifts subsequent line numbers), prints what it assigned,
  then lists.
- Tests: extended `tests/test_ideas.py` with sequential assignment, id-first-in-drawer,
  gap-safe numbering, selector normalization (case + padding), reindex idempotence, id column
  in `wt ideas`, and CLI echo/`--reindex` coverage. `uv run pytest` all green (190 passed);
  `python3 tools/spec_lint.py` exits 0.
- Manual verification (tmp org + tmp specs dir): captured 3 ideas → `IDEA-001..003`;
  `wt spec new --from-idea IDEA-001` and `--from-idea idea-2` both resolved correctly;
  `wt ideas --reindex` backfilled a pre-existing id-less idea to `IDEA-004` and a second run
  reported nothing to do.
