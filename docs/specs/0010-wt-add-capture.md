---
id: SPEC-0010
title: "`wt add` — capture work items"
status: done
owner: user
created: 2026-07-16
updated: 2026-07-16
milestone: "M2: tasks"
kind: feature
tags: [tasks, org, cli]
depends_on: [SPEC-0005, SPEC-0009]
---

## Context

The [SPEC-0004](./0004-org-task-management.md) epic shipped read-only task views plus one
narrow write path — TODO-state mutation of *existing* headlines
([SPEC-0009](./0009-todo-state-write-back.md)). **Creating** tasks was an explicit non-goal
there (get the read spine + safest mutation proven first). The natural next step is to
capture work items from the CLI so a JIRA-keyed task can be added and immediately join
tracked time in `wt digest` (its `topic_key` is derived from the headline —
[SPEC-0005](./0005-org-parser-and-task-model.md)). This is a follow-on to the (closed) epic,
modeled as a standalone feature spec building on its `org`/`org_write` foundation.

## Goals / Non-goals

**Goals**
- `wt add "<text>"` appends a well-formed org headline to a capture file, with optional
  `--state`, `--tag` (repeatable), `--priority`, `--scheduled`, `--deadline`, and `--file`.
- State is validated against the **target file's** keyword set; default = the file's first
  active keyword. A JIRA key in the text auto-becomes the task's `topic_key` on read.
- Reuse SPEC-0009's backup + atomic-write; create the capture file if it doesn't exist.

**Non-goals**
- `--project`: `Task.project` is *derived* from outline structure (nearest level-1 ancestor,
  else file stem), not a property — so grouping is chosen via `--file`/the capture file, not a
  flag. (A future spec could add structural placement under a category heading.)
- Editing/refiling/deleting existing tasks, or multi-line bodies/properties on capture.
- Interactive capture UI. One headline per invocation (a `-` stdin mode may come later).

## Decision

Add `org_write.add_task(cfg, text, *, state, tags, priority, scheduled, deadline, file)` that
builds a single level-1 headline and appends it to the target file (default
`cfg["org_capture_file"]`, seeded to `~/work/org/inbox.org`). A `@cli.command("add")` handler
wires it with a `nargs=-1` text argument (so `wt add DEMO-100 do the thing` needs no quotes).

## Design

### Config (`src/wt/config.py`)

Add `"org_capture_file": "~/work/org/inbox.org"` to `DEFAULT_CONFIG` — the default append
target. It lives under `~/work/org`, so captured tasks are visible to `load_tasks` at once.

### `org_write.add_task(...)`

- **Target:** `file or cfg["org_capture_file"]` (expanduser).
- **Keyword set:** if the file exists, `file_keywords(cfg, path)`; else the
  `org_todo_keywords` fallback. Default `state` = first active keyword (e.g. `TODO`). A
  provided `state` must be in `active | done`, else `ValueError` listing valid states.
- **Headline:** `* {STATE}{ [#P]}{ text}{ :t1:t2:}` — state, optional priority cookie, the
  text, then grouped tags (org `:a:b:` form) if any. Whitespace normalized to single spaces.
- **Planning line:** if `scheduled`/`deadline` given, a following
  `  SCHEDULED: <YYYY-MM-DD Ddd>[ DEADLINE: <…>]` line (dates parsed via
  `dates.parse_date`, formatted org-style with weekday).
- **Append:** ensure the existing content ends with a newline, then append the headline
  (+ planning line). If the file is new, create it (no backup — nothing to back up); if it
  exists, back it up first. Write atomically (reuse `_atomic_backup_write`, guarded so a
  missing original is simply created rather than erroring on the backup copy).
- **Returns** `(path, headline_line)` for the CLI to echo.

### CLI (`src/wt/cli.py`)

```
wt add DEMO-100 wire up the thing
wt add "fix the flaky test" --priority A --tag ci --tag flaky
wt add "prep review" --scheduled 2026-07-20 --file ~/work/org/agenda.org
wt add "triage" --state TRIAGE          # validated against the file's #+TODO
```

Options: `--state`, `--tag` (multiple), `--priority`, `--scheduled`, `--deadline`, `--file`.
`ValueError` → `click.ClickException`. Prints a `✓` confirmation with the created headline +
path (like `wt state`/`wt done`).

## Alternatives considered

- **`--project` flag** — rejected for v1; project is structural/derived, so a flag would
  silently not round-trip. Grouping is via `--file` instead.
- **A dedicated capture format/drawer** — unnecessary; a plain top-level headline is what the
  read path already models and what org users expect in an inbox.
- **Reopening the SPEC-0004 epic to host this** — rejected; the epic shipped as scoped. A
  standalone spec keeps the epic's history truthful and the linter green at every commit.

## Acceptance criteria

- [x] `wt add "<text>"` appends a valid headline to the capture file; `wt tasks` then shows it.
- [x] Default state is the target file's first active keyword; `--state` is validated against
      that file's set (invalid → error, no write).
- [x] `--tag` (repeatable), `--priority`, `--scheduled`, `--deadline`, and `--file` are honored
      and produce org-valid output (re-parses via `orgparse`/`load_tasks`).
- [x] A JIRA key in the text becomes the task's `topic_key` (so it joins `wt digest`) —
      verified: captured `DEMO-100` shows up in `filter_tasks(has_key=True)`.
- [x] The capture file is created if missing; an existing file is backed up before append and
      written atomically; unrelated content is untouched.

## Test plan

- **Automated:** `tests/test_org_add.py` (tmp org dir): assert a captured task re-parses with
  the expected `state`/`tags`/`priority`/`scheduled`/`deadline`/`topic_key`; default-state =
  first active keyword; invalid `--state` raises and writes nothing; append preserves existing
  lines (byte-equality of the prefix) and adds exactly the new headline (+ planning line);
  a missing file is created (no backup) while an existing one gets a backup. CLI via
  `CliRunner` (exit code + confirmation; error path for bad state).
- **Manual verification:** on a **temp** cfg (not the real inbox), `wt add DEMO-100 demo` then
  `wt tasks --key` shows `DEMO-100`; confirm the file is org-valid.
- **Regression guard:** `uv run pytest` stays green; read path + `wt state`/`done` untouched.

## Rollout / migration

1. `org_capture_file` config default.
2. `org_write.add_task` (+ backup guard for new files).
3. `wt add` CLI handler.
4. Tests + manual check on a temp dir; close the loop.

**What shipped / deviations:**
- `_atomic_backup_write` now skips the backup when the target doesn't exist (new capture file)
  and `makedirs` the parent — so `add_task` creates the file cleanly with no spurious backup.
- Headline shape: `* {STATE}{ [#P]}{ text}{ :tags:}`; an optional `  SCHEDULED: <…>[ DEADLINE:
  <…>]` planning line follows. Dates via `dates.parse_date` → org `<YYYY-MM-DD Ddd>`.
- `--project` intentionally omitted (project is derived from structure; use `--file`).
- **Test-suite note:** the earlier task **wipe** emptied the real `~/work/org`, which surfaced
  a brittle assumption in the SPEC-0004 integration test (it asserted the live tree contained
  both done and open tasks). That assertion was wrong to make on mutable user data; it was
  replaced with an environment-independent invariant (done ⇒ has a state keyword).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 66 passed;
      `tests/test_org_add.py` covers create/options/JIRA-key/default-state/invalid/append+backup/
      new-file/CLI); manual `add_task` check on a temp dir.
- [x] No regressions (also hardened the SPEC-0004 integration test against empty trees).
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
