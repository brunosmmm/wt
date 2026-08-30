---
id: SPEC-0074
title: "normalize-logs/normalize-questions: scan every idea-bearing file"
status: done
owner: user
created: 2026-07-26
updated: 2026-07-26
source_idea: IDEA-086
parent: SPEC-0070
milestone: "M4: cli ergonomics"
tags: [org, maintenance]
depends_on: [SPEC-0071, SPEC-0072]
---

## Context

Promoted from idea `IDEA-086` (SPEC-0074).

  :PROPERTIES:
  :ID: IDEA-086
  :EPIC: SPEC-0070
  :END:
** Summary
Child of epic `SPEC-0070`.

SPEC-0074 — Fix `normalize-logs`/`normalize-questions` (no-selector mode) to scan every
** Open questions

** Log

## Goals / Non-goals

**Goals**
- `wt idea normalize-logs`/`normalize-questions`, when called with no selector, currently
  hardcode operating against the single `cfg['org_ideas_file']` path
  (`explore.py::normalize_idea_log_stamps`/`normalize_idea_questions`, ~L317-322, ~L391-395).
  Fix both to enumerate every distinct file any idea currently lives in (active file, rotated
  historical files from SPEC-0071, the archive file from SPEC-0072/0073) via `load_tasks`,
  instead of one hardcoded path.
- No CLI changes needed: both commands already print per-`(path, n)` results from a *list*
  returned by these functions (`cli.py`'s existing loop), so returning more list entries just
  works.

**Non-goals**
- Not changing either function's per-idea normalization logic — only the *no-selector
  enumeration* changes; a selector-scoped call (`normalize-logs IDEA-020`) is untouched.
- Not changing CLI output formatting/verbosity.

## Decision

Replace each function's no-selector branch — which currently resolves a single hardcoded path —
with a scan of `load_tasks(cfg)` grouped by the real file each idea currently lives in, so the
existing per-file normalization logic runs once per distinct file instead of once against one
assumed path.

## Design

- **`explore.py::normalize_idea_questions(cfg, selector=None)`** (~L309-341): the no-selector
  branch changes from:
  ```python
  path = cfg.get("org_ideas_file")
  ...
  ids = [... for tk in load_tasks(cfg) if tk.is_idea and os.path.realpath(tk.file) == path]
  ```
  to grouping every idea by its real file:
  ```python
  from collections import defaultdict
  by_file = defaultdict(list)
  for tk in load_tasks(cfg):
      if tk.is_idea:
          by_file[os.path.realpath(tk.file)].append(tk.properties.get("ID") or tk.id)
  file_groups = sorted(by_file.items())
  ```
  The existing per-idea normalization loop (`for iid in ids: ...`) is unchanged, just now
  wrapped in an outer `for path, ids in file_groups:` loop, accumulating one `(path, n)` per
  file instead of a single-element list.
- **`explore.py::normalize_idea_log_stamps(cfg, selector=None)`** (~L380-396): since
  `normalize_log_stamps_in_file` already operates on one whole file, the no-selector branch
  simplifies to:
  ```python
  paths = sorted({os.path.realpath(tk.file) for tk in load_tasks(cfg) if tk.is_idea})
  return [(p, normalize_log_stamps_in_file(cfg, p)) for p in paths]
  ```
- **No `cli.py` changes** — `idea_normalize_logs_cmd`/`idea_normalize_questions_cmd` already
  iterate `for path, n in results:` over whatever list length these functions return.

## Alternatives considered

- **Keep a single-file assumption, add a `--all-files` flag** — rejected: the whole point of
  SPEC-0070's design is that idea-bearing files are already transparently plural (rotation,
  archival); requiring a flag to opt into correct behavior just reintroduces the same silent-gap
  risk these commands already had.

## Acceptance criteria

- [x] With ideas split across the active file, a rotated historical file, and the archive file,
      running `normalize-logs`/`normalize-questions` with no selector processes all three,
      returning one `(path, n)` entry per file.
- [x] A selector-scoped call (`normalize-logs IDEA-020`) is unaffected — still touches only that
      idea's file.
- [x] The common case (all ideas still in one file) behaves identically to before.
- [x] The existing CLI commands require no changes and correctly display results across
      multiple files.

## Test plan

- **Automated tests:** `tests/test_questions_state.py` (shipped location) — seed ideas across
  two distinct files (simulating post-rotation/archival), run both no-selector normalize
  functions, and assert each file gets its own `(path, n)` entry with correct per-file counts;
  the existing lossless/idempotent single-file test continues to pass unchanged (regression).
- **Manual verification:** run `wt idea normalize-logs`/`normalize-questions` against the real
  `~/work/org` tree (read-mostly operation, idempotent) and confirm no errors and sane output
  now that a rotated/archive file may exist alongside `ideas.org`.
- **Regression guard:** full `uv run pytest` green.

## Rollout / migration

1. No hard code dependency on SPEC-0071/0072, but sequenced after them since there's nothing
   real to test multi-file behavior against until they exist.
2. Pure function-body change; no data migration.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

- None blocking.
