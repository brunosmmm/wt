---
id: SPEC-0009
title: TODO-state write-back
status: done
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M2: tasks"
kind: feature
tags: [tasks, org, cli]
parent: SPEC-0004
depends_on: [SPEC-0005, SPEC-0006]
---

## Context

The final, deliberately-isolated capability of the [SPEC-0004](./0004-org-task-management.md)
epic: **mutating** a task's TODO state in the org file (e.g. `TODO → INPROGRESS → DONE`).
`orgparse` is **read-only**, so this is custom code we own, gated behind everything else so
the read-only spine is proven first. Identity comes from
[SPEC-0005](./0005-org-parser-and-task-model.md)'s `Task.id`, and task selection reuses
[SPEC-0006](./0006-wt-tasks-list-filter.md)'s filtering.

## Goals / Non-goals

**Goals**
- `wt done <selector>` / `wt state <selector> <STATE>` to change a single task's TODO state
  safely, validating the new state against that **file's** keyword set.
- Round-trip fidelity: only the one headline's keyword changes; no other bytes move.
- A backup of the file before writing; a `CLOSED:` stamp added/removed when moving to/from a
  done state (matching org behavior), guarded by a flag.

**Non-goals**
- Editing anything other than the TODO keyword (no re-tagging, priority, body, scheduling).
- Bulk/interactive multi-task mutation. One task per invocation in v1.
- Creating new tasks or files.

## Decision

Add `src/wt/org_write.py` with `set_state(cfg, task, new_state, *, stamp_closed=True) ->
path` that rewrites exactly the headline line of `task.file:task.line`. Selection resolves a
selector (an `:ID:`, a `file:line`, or a unique JIRA key / heading substring) to exactly one
`Task` via `load_tasks` + `filter_tasks`; ambiguous or absent selectors error out without
writing. Validate `new_state` ∈ that file's keyword set. Write via a temp file + atomic
replace, after copying the original to a timestamped backup under `cfg["data_dir"]`.

## Design

### Mutation (`src/wt/org_write.py`)

- Re-read the file fresh (don't trust a stale parse). Locate the target headline by
  `task.line` **and** verify the line still starts with the expected stars + old state
  (guard against drift; error if mismatched).
- Rewrite only the keyword token: `* OLD rest` → `* NEW rest` (or insert/remove the keyword
  when moving from/to a plain headline). Preserve indentation, priority cookie, tags, and
  trailing whitespace exactly.
- **CLOSED stamp:** when `stamp_closed` and moving into a done state, insert a
  `   CLOSED: [YYYY-MM-DD ...]` line under the headline (org format); when moving out of done,
  remove an existing `CLOSED:` line. `--no-closed` disables.
- **Backup + atomic write:** copy original → `cfg["data_dir"]/org-backups/<file>.<ts>.bak`;
  write new content to a temp file in the same dir; `os.replace` over the original.
- Return the path; the CLI prints a confirmation like the `override`/`map` handlers.

### Validation

- `new_state` must be in the file's active-or-done keyword set (parsed from `#+TODO`, falling
  back to `org_todo_keywords`). Unknown state ⇒ error listing valid states.
- Selector must resolve to exactly one task ⇒ else error (`no task matched` / `ambiguous:` +
  the candidates).

### CLI (`src/wt/cli.py`)

```
wt state <selector> <STATE>   set TODO state (validated against the file)
wt done <selector>            shorthand: set to the file's first done keyword
```

`--no-closed` flag on both; `@click.pass_obj`.

## Alternatives considered

- **Regex-replace the whole file text** — rejected; too easy to hit a duplicate headline.
  Line-anchored + old-state verification is safer.
- **Fork/patch orgparse to write** — rejected; heavier than owning a tiny, well-tested
  line rewrite; we only mutate one token.
- **No backup (rely on git)** — rejected; org files may not be in a repo. A local backup is
  cheap insurance; git users still get their diff.

## Acceptance criteria

- [x] `wt state <sel> <STATE>` changes exactly the target headline's keyword and nothing else
      (byte-diff limited to that line ± the CLOSED line — verified on a real-file copy).
- [x] Invalid state or ambiguous/no-match selector errors **without** writing.
- [x] Moving to a done state stamps `CLOSED:` (unless `--no-closed`); moving out removes it.
- [x] A backup of the original is written before mutation; the write is atomic.
- [x] `wt done <sel>` sets the file's first done keyword.

## Test plan

- **Automated:** `tests/test_org_write.py` copies a fixture into a tmp dir, runs `set_state`,
  and asserts: (a) re-parsing shows the new state; (b) the file diff touches only the headline
  (± CLOSED); (c) round-trip `TODO→INPROGRESS→DONE→TODO` restores original modulo the CLOSED
  stamp; (d) invalid state raises and leaves the file unchanged; (e) ambiguous selector raises;
  (f) a backup file exists. CLI via `CliRunner` (exit codes + messages).
- **Manual verification:** on a **copy** of a real `~/work/org` file, `uv run wt state
  DEMO-504 DONE` then `git diff`/`diff` confirms a one-line change + CLOSED stamp; re-open in
  Emacs org confirms it's still valid.
- **Regression guard:** `uv run pytest` stays green; read path (0005–0008) unaffected.

## Rollout / migration

1. `src/wt/org_write.py` (`set_state` + selector resolution + backup/atomic write).
2. `wt state` / `wt done` CLI handlers.
3. Tests (incl. round-trip + failure cases) + manual check on a copy; close the loop.
4. Epic done-gate: with 0005–0009 done, SPEC-0004 can move to `done`.

**What shipped / deviations:**
- `src/wt/org_write.py`: `set_state`, `set_state_by_selector`, `mark_done`, `resolve_selector`,
  `file_keywords`. Selector precedence: exact `id` (covers `:ID:` and `file:line`) → exact
  `topic_key` → case-insensitive heading substring; no/ambiguous match raises without writing.
- The CLOSED stamp is `CLOSED: [YYYY-MM-DD Ddd]` (date + weekday, matching the user's real
  files), indented `len(stars)+1` spaces, and is only managed on the line **immediately** below
  the headline (the common layout); `--no-closed` disables. Priority cookies/tags/body are
  preserved (drift guard verifies the on-disk keyword before rewriting).
- Verified on a copy of the real `estimations.org`: `wt state DEMO-504 DONE` produced a
  2-line diff (keyword + inserted CLOSED), nothing else moved.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 55 passed;
      `tests/test_org_write.py` covers one-line diff, round-trip, CLOSED add/remove, invalid/
      ambiguous/no-match guards, backup, `wt done`, CLI); manual real-file-copy check performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
