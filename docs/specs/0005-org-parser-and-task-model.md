---
id: SPEC-0005
title: Org config + parser & Task model
status: done
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M2: tasks"
kind: feature
tags: [tasks, org]
parent: SPEC-0004
---

## Context

The foundation of the [SPEC-0004](./0004-org-task-management.md) epic: turn the user's
org-mode files into a normalized, read-only `Task` model that every other child spec queries.
Nothing in `wt` parses org today. The real `~/work/org/` tree has **per-file** `#+TODO`
keyword sets, **grouped tags** (`:projects:demo:`), JIRA keys **in the headline text**
(`* INPROGRESS DEMO-100`), `:PROPERTIES:` drawers, and `CLOSED` timestamps.

## Goals / Non-goals

**Goals**
- Add `orgparse` as a runtime dependency and a new `src/wt/org.py` module.
- Config: `org_files` (sources) + optional `org_todo_keywords` (fallback keyword set).
- A `Task` dataclass and `load_tasks(cfg)` producing a flat `list[Task]` from the sources,
  with per-file done-state resolution, grouped-tag splitting, and `topic_key` extraction.

**Non-goals**
- Any CLI command or rendering (SPEC-0006/0007) — this spec is parser + model + tests only.
- Writing org files (SPEC-0009). Parsing is strictly read-only here.
- A `filter_tasks` UI; a minimal query helper is fine but rich filtering is SPEC-0006.

## Decision

Use `orgparse.load(path, env=OrgEnv(todos=..., dones=...))` for parsing. `Task` is a frozen
`@dataclass`. `load_tasks(cfg)` expands `cfg["org_files"]` (files/dirs/globs; dirs →
`**/*.org`, excluding any path under `~/.emacs.d`), loads each file, and flattens every
node with a headline into a `Task`. Per-file `#+TODO` is honored by orgparse natively; files
lacking it fall back to `org_todo_keywords` (or a built-in default) seeded into `OrgEnv`.

## Design

### Dependency

Add `"orgparse>=0.4"` to `pyproject.toml` `[project].dependencies`. Refresh `uv.lock`.

### Config (`src/wt/config.py`)

Add to `DEFAULT_CONFIG`:
- `"org_files": ["~/work/org"]` — list of files/dirs/globs.
- `"org_todo_keywords": ["TODO", "|", "DONE"]` — fallback for files with no `#+TODO`
  (the `"|"` splits active from done keywords, mirroring org syntax).

The existing `load_config` merge already **replaces** non-dict values on user override, so a
user-supplied `org_files` list replaces the default (confirmed desired). Paths are expanded
with `os.path.expanduser` at use-time in `org.py` (not stored as `_`-prefixed keys), keeping
`config.py` unchanged beyond the two new defaults.

### `src/wt/org.py`

```python
@dataclass(frozen=True)
class Task:
    id: str
    heading: str
    state: str | None
    is_done: bool
    tags: frozenset[str]
    priority: str | None
    properties: dict[str, str]
    scheduled: datetime.date | None
    deadline: datetime.date | None
    closed: datetime.date | None
    level: int
    project: str
    file: str
    line: int
    topic_key: str | None
```

- **Source expansion** `_iter_org_paths(cfg) -> list[Path]`: for each entry, expanduser; a
  file ⇒ itself; a dir ⇒ `sorted(rglob("*.org"))`; a glob ⇒ its matches. Skip anything under
  `~/.emacs.d`. De-dupe, stable order.
- **Loading:** `orgparse.load(path, env=OrgEnv(...))`. Seed `OrgEnv` from the resolved
  fallback keyword set for files without `#+TODO` (orgparse reads in-file `#+TODO` itself; the
  env is the fallback).
- **done resolution:** a node is `is_done` when its `todo` keyword is in that file's done set.
  Prefer orgparse's own done-keyword knowledge (`node.env` done keywords); the fallback set is
  used only when the file declares none.
- **tags:** union of the node's own tags; grouped `:a:b:` already split by orgparse into
  individual tags — normalize to a `frozenset`.
- **priority:** from orgparse (`[#A]`), else `None`.
- **properties:** `dict(node.properties)`.
- **scheduled/deadline/closed:** orgparse exposes these; coerce to `datetime.date` (date part).
- **project:** nearest ancestor heading that is a *category* (a top-level heading, level 1)
  → its cleaned heading text; else the file stem.
- **id:** `properties["ID"]` if present, else `f"{file}:{line}"`.
- **topic_key:** first of properties `TOPIC`/`JIRA`/`REPO` if present; else
  `topics.KEY_RE.search(heading)` group(1); else `None`.

Public API: `load_tasks(cfg) -> list[Task]` and a light `filter_tasks(tasks, *, state=None,
tag=None, project=None, priority=None, done=None) -> list[Task]` used later by SPEC-0006.

## Alternatives considered

- **Hand-rolled org parser** — rejected; per-file `#+TODO`, drawers, and tag grouping are
  fiddly and `orgparse` already handles them, is BSD-2, and maintained.
- **`:JIRA:` property as the only link** — rejected; the user's real files put keys in
  headlines, so headline-parse must be the default with property override as the escape hatch.
- **Storing expanded org paths as `cfg["_org"]`** — unnecessary; expansion is cheap and local
  to `org.py`, keeping `config.py` minimal.

## Acceptance criteria

- [x] `orgparse` is a declared runtime dependency; `uv run python -c "import orgparse"` works.
- [x] `DEFAULT_CONFIG` has `org_files` and `org_todo_keywords`; a user `org_files` list
      replaces (not merges) the default.
- [x] `load_tasks(cfg)` returns `Task`s from fixture files with **different** `#+TODO` sets,
      each task's `is_done` computed against its **own file's** done keywords.
- [x] Grouped tags (`:projects:demo:`) split into individual tags; priority, `CLOSED`, and
      `:PROPERTIES:` are captured.
- [x] `topic_key` = JIRA key from the headline (`DEMO-100`), overridden when a
      `:TOPIC:`/`:JIRA:`/`:REPO:` property is present.
- [x] `id` uses `:ID:` when present, else `file:line`.

## Test plan

- **Automated:** `tests/test_org.py` with fixtures under `tests/fixtures/org/` mirroring the
  user's real files: one with `TODO INPROGRESS | DONE CANCELED`, one with the longer
  `agenda.org` set, one with grouped tags + priority + `CLOSED`, one with a JIRA-in-headline
  task, and one exercising the `:TOPIC:`/`:JIRA:`/`:REPO:` property override. Assert per-file
  `is_done`, tag splitting, `topic_key` (headline + override), `id` fallback, and `project`
  derivation. Also assert `org_files` list-replace semantics via a synthesized cfg.
- **Manual verification:** `uv run python -c "from wt.config import load_config; from wt.org
  import load_tasks; print(len(load_tasks(load_config())))"` against real `~/work/org` prints
  a plausible count; spot-check a few `Task` reprs.
- **Regression guard:** `uv run pytest` — the pre-existing suite (aggregate/ingest/paths/specs)
  must stay green; adding a dependency must not break imports.

## Rollout / migration

1. Add `orgparse` to `pyproject.toml`; `uv lock`/`uv sync`. *(shipped: `orgparse==0.4.20251020`)*
2. Add the two config defaults.
3. Write `src/wt/org.py` + fixtures + `tests/test_org.py`.
4. Close the loop (tests pass, spec updated, ledger regenerated).

**What shipped / deviations:**
- `orgparse.load(path, env=OrgEnv(...))` **requires** the env's `filename` to equal the path
  (else `ValueError`), so `load_tasks` builds a fresh `OrgEnv(todos, dones, filename=path)`
  per file. A file's own `#+TODO` still wins; the seeded env is only the fallback (verified).
- `tags` uses orgparse's **inherited** tag set (`node.tags`), matching org-agenda semantics
  (a child under `:projects:` inherits it), grouped tags already split — better for filtering
  than own-tags-only.
- `filter_tasks` exposes `done=` and `has_key=` bools (SPEC-0006 maps `--all`→`done=False`
  default and `--key`→`has_key=True`).
- `project` walks `node.parent` to the nearest **level-1** heading; a top-level task falls back
  to the file stem (confirmed on real data: `DEMO-100` → `estimations`).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 27 passed); manual step
      performed (`load_tasks` over real `~/work/org`: 95 tasks, `DEMO-100`/`DEMO-100` keyed).
- [x] No regressions (pre-existing 12 tests still pass).
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
