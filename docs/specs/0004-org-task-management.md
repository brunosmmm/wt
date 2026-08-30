---
id: SPEC-0004
title: Org-mode task management
status: done
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M2: tasks"
kind: epic
tags: [tasks, org, reporting]
---

## Context

`wt` today passively tracks *time* per topic from Claude/Cursor transcripts + meetings
(base topics = JIRA key / repo / repo:branch / loose label). It has no notion of **what
work is planned or in flight** — that lives in the user's **org-mode** files under
`~/work/org/`. The strategic payoff: those org headlines already carry the same JIRA keys
`wt` uses as topic keys (`* INPROGRESS DEMO-504`), so we can **join already-tracked time to
tasks with zero manual clocking**.

This is a large, multi-part feature (parse + model, list/filter, agenda, time join, digests,
write-back), so it is modeled as an **epic** with child specs using the
[SPEC-0003](./0003-epic-and-subspec-model.md) hierarchy machinery.

Findings from exploring the real `~/work/org/` that shape the design:
- `#+TODO:` keyword sets are **per-file** (e.g. `TODO TRIAGE BLOCKED INPROGRESS LONGTERM |
  NONACTIONABLE DONE WONTDO CANCELED` in `agenda.org`; `TODO INPROGRESS | DONE CANCELED` in
  `estimations.org`; `CATEGORIZE REFILE TODO | DONE DISCARDED` in `inbox.org`).
- Tags are **grouped** (`:projects:demo:`), nesting is shallow (≤2).
- **JIRA keys live in the headline text** (`* INPROGRESS DEMO-504`), *not* in properties.
- Properties exist but are domain-specific (`:OriginalPoints:`), `CLOSED` is used, and there
  is **no** scheduling/clocking data yet.
- Subdirectories exist (`ai/`, `ats/`, `journal/`, …) holding more `.org` files.

## Goals / Non-goals

**Goals**
- A read-only, normalized **Task** model parsed from the user's org files, respecting
  per-file TODO keyword sets, grouped tags, priorities, `CLOSED`, and JIRA-in-headline.
- `wt tasks` (list/filter) and `wt agenda` (date views) as the **v1 must-haves**.
- Join `wt`'s tracked time to tasks by JIRA key (`topic_key`), and status+time **digests**.
- Safe TODO-state **write-back** as the final, isolated capability.

**Non-goals**
- A general org editor or agenda replacement for Emacs. `wt` reads a useful subset.
- Clocking/`LOGBOOK` semantics (org clock entries) — time comes from `wt`'s own tracking.
- Parsing arbitrary org constructs (tables, babel, drawers beyond `:PROPERTIES:`).
- Writing anything other than TODO state in v1 (see SPEC-0009 scope).

## Decision

Ship a **read-only spine first**, TODO-state write-back last. Add `orgparse` (BSD-2,
maintained) as a runtime dependency for parsing — it covers the needed subset including
per-file `#+TODO`, but is read-only, so write-back (SPEC-0009) is custom code we own.
Linking is by **headline JIRA key (auto) + optional `:TOPIC:`/`:JIRA:`/`:REPO:` property
override**. All child specs share one new module `src/wt/org.py` and the shared config /
rendering / CLI conventions below.

## Architecture / cross-cutting design

**New module `src/wt/org.py`** — parsing + the normalized model + query/filter. A `Task`
dataclass with fields:

- `id` — `:ID:` property if present, else `f"{file}:{line}"`.
- `heading` — the headline text with the TODO keyword/priority/tags stripped.
- `state` — the raw TODO keyword (or `None` for a plain headline).
- `is_done` — whether `state` is in the file's *done* keyword set (the keywords right of
  `|` in that file's `#+TODO`, falling back to a global default set).
- `tags` — a `set[str]` with grouped tags split (`:projects:demo:` → `{"projects","demo"}`).
- `priority` — `A`/`B`/`C` or `None`.
- `properties` — `dict[str,str]` from the `:PROPERTIES:` drawer.
- `scheduled` / `deadline` / `closed` — `datetime.date` or `None`.
- `level` — outline depth (1-based).
- `project` — nearest ancestor *category* heading, else the file stem.
- `file`, `line` — source location.
- `topic_key` — JIRA key parsed from the heading via `topics.KEY_RE`, **overridable** by a
  `:TOPIC:`/`:JIRA:`/`:REPO:` property (first present wins, in that order).

Loading uses `orgparse.load(path, env=OrgEnv(...))`, seeding `OrgEnv` with an optional global
`org_todo_keywords` for files lacking a `#+TODO` line. A top-level `load_tasks(cfg)` expands
the configured sources into a flat `list[Task]`, plus a `filter_tasks(...)` query helper.

**Config** (`src/wt/config.py:DEFAULT_CONFIG`): add `"org_files": ["~/work/org"]` (a list of
files / dirs / globs; dirs expand to `**/*.org`, excluding `~/.emacs.d`) and optional
`"org_todo_keywords"` (a `["TODO", ... "|", "DONE", ...]`-shaped default). **Lists replace
on user override** (confirmed behavior — the existing merge only deep-merges dicts). No
`paths.py` change — reuse `cfg["data_dir"]` for any parsed cache.

**Rendering** (`src/wt/report.py`): new `tasks(...)`/`agenda(...)` reuse `_scope_days`,
`_topic_style`, `_bar`, `Panel`, and the shared `console`; task tables mirror the 4-column
`topics()` table shape.

**CLI** (`src/wt/cli.py`): new `@cli.command` handlers `wt tasks` and `wt agenda`, each with
`@click.pass_obj`, the positional `date` + `-w/--week` + `--last` convention, and the `"now"`
sentinel via `dates.parse_date`.

**Time join** (SPEC-0008): match `Task.topic_key` against `aggregate.assemble(cfg)` →
`data[day]["topics"] = {base_topic: secs}`; optionally expose task-as-facet-axis reusing
`report._regroup` / `rules.load_mappings`.

## Breakdown / sub-specs

- [x] SPEC-0005 — Org config + parser & Task model (foundation; `orgparse` dep, `org_files`
  config, per-file `#+TODO`, grouped tags, `topic_key`). *(no deps)*
- [x] SPEC-0006 — `wt tasks` list & filter by state/tag/project/priority. *(depends_on 0005)* — **v1**
- [x] SPEC-0007 — `wt agenda` date views (today/week by SCHEDULED/DEADLINE + overdue). *(depends_on 0005)* — **v1**
- [x] SPEC-0008 — Time→task join & digests (hours per task/project; daily/weekly digest). *(depends_on 0005)*
- [x] SPEC-0009 — TODO-state write-back (safe mutation, `:ID:` identity, backup, round-trip). *(depends_on 0005, 0006)* — last

Sequencing: 0005 → {0006, 0007} (v1, parallelizable) → 0008 → 0009.

## Acceptance criteria

- [x] `src/wt/org.py` parses the real `~/work/org/` tree into `Task`s with correct per-file
      done-state resolution, grouped-tag splitting, and `topic_key` extraction.
- [x] `wt tasks` and `wt agenda` run against the real tree and render useful output.
- [x] For a task with a JIRA key, `wt`'s joined hours (SPEC-0008) equal that topic's hours in
      `wt report` for the same scope (verified: DEMO-817 = 14.0976h both ways).
- [x] TODO-state write-back (SPEC-0009) round-trips a file with no unintended diff.
- [x] All child specs are `done`/`superseded`.

## Test plan

- **Integration/e2e:** with the child unit suites green, an integration check parses the real
  `~/work/org/` (guarded to skip if absent) and asserts: (a) tasks are found across multiple
  files with differing `#+TODO` sets; (b) a known JIRA-keyed task (`DEMO-504`) yields
  `topic_key == "DEMO-504"`; (c) the join sanity check — a task's joined hours equal that
  topic's `wt report` hours for the same scope.
- **Manual verification:** `uv run wt tasks`, `uv run wt agenda`, and a digest run against
  `~/work/org`, eyeballed for correctness.
- **Spec system:** `python3 tools/spec_lint.py` stays green; epic done-gating enforces all
  children finished before SPEC-0004 → `done`; `tests/test_specs.py` in the pytest run.

## Rollout / sequencing

Children land in the order above. Partial delivery is useful: after 0005+0006+0007 the user
has read-only task list + agenda (v1); 0008 adds the time join / digests; 0009 adds mutation.
Each child closes its own loop per `AGENTS.md` before the next starts.

## Definition of done

- [x] All child specs `done` or `superseded` (the linter gates this).
- [x] Integration test plan executed; `uv run pytest` green (57 passed; `tests/test_org_integration.py`
      parses the real tree + checks the join invariant, guarded to skip where absent).
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

_None._
