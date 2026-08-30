---
id: SPEC-0134
title: "Mtime-cached load_tasks and non-blocking desk reload"
status: done
owner: user
created: 2026-08-28
updated: 2026-08-28
source_idea: IDEA-288
milestone: "M5: interactive desk"
tags: [tui, performance, org]
depends_on: [SPEC-0128, SPEC-0129]
---

## Context

Promoted from idea `IDEA-288`. Follow-up to the work deliberately descoped in
[SPEC-0129](./0129-tui-poll-reload-off-the-event-loop-thread.md) (IDEA-232 Q4): that fix moved
poll-triggered `load_rows` off the Textual event loop but left `org.load_tasks` uncached and
left manual / mutation-driven `IdeaDesk.reload()` synchronous.

Measured on the live corpus (22 org files, ~915KB, ~602 tasks, ~80 active ideas) **before**
this change:

- `org.load_tasks` ≈ **0.7–0.9s** every call (no cache).
- `wt.tui.model.load_rows` ≈ **0.74s**.
- Every `j`/`k` ran `show_detail` → `_resolve_fresh` → `resolve_selector` → `load_tasks`
  (~**700ms per key**), blocking input/rendering.
- Detail render / list paint cells ≈ 1–7ms — not the problem.

[SPEC-0128](./0128-tui-desk-resilience-to-external-idea-updates.md) correctly requires detail
reads to resolve from disk so line-number drift cannot trip `explore._idea_span`. That
invariant does **not** require re-parsing when the corpus mtime signature is unchanged.

## Goals / Non-goals

**Goals**

- Unchanged org corpus: a second `load_tasks` in the same process returns without re-parsing.
- After any org file mtime change (or path add/remove), the next `load_tasks` re-parses and
  returns fresh `Task`s (SPEC-0128 freshness preserved).
- TUI `j`/`k` with an unchanged corpus does not block the event loop on a full reparse.
- Manual `r`, search, filter, sort, and post-mutation desk reloads no longer block the event
  loop on `load_rows` (same executor + in-flight pattern as SPEC-0129's poll path).

**Non-goals**

- Rewriting orgparse or incremental per-file parse.
- Dropping SPEC-0128 drift guards or the external-change poll.
- Changing the 1.5s poll interval.
- Speeding pygments detail lexing.

## Decision

1. **`org.load_tasks` gains a process-local cache** keyed by
   `(org_files_mtime_signature(cfg), org_todo_keywords, org_idea_keywords)`. Hit → return a
   new `list` of the same `Task` objects. Miss → parse as today. Expose
   `invalidate_tasks_cache()` for tests and explicit bust. Keywords are part of the key
   because they shape `is_idea` / `is_done` / enrichment filtering — same bytes under a
   different vocabulary must not reuse Tasks.
2. **All desk `reload` paths share SPEC-0129's executor pattern.** `_reload_async` awaits
   `M.load_rows` via `run_in_executor`, guarded by `_reload_in_flight`. Sync `reload()`
   schedules it with Textual `run_worker` when a loop is running; falls back to blocking
   `_reload_blocking` otherwise. Poll `_check_external_changes` awaits the same helper.

This extends past SPEC-0129's non-goal ("leave sync reload sync") without superseding
SPEC-0129's poll-threading decision.

## Design

**`src/wt/org.py`** — `_load_tasks_cache_key`, `invalidate_tasks_cache`, cached `load_tasks`.

**`src/wt/tui/app.py`** — `reload` → `run_worker(_reload_async)`; `_reload_blocking` for
no-loop; `_check_external_changes` keeps signature compare + external hint, then
`await self._reload_async(...)`.

`show_detail` still calls `_resolve_fresh` (SPEC-0128); with a warm cache that is near-free.

## Alternatives considered

- **TUI-only: reuse `_pairs` Task when signature unchanged** — helps j/k only; every other
  `resolve_selector` / CLI / hub path still re-parses. Lost to the library cache.
- **Cache only inside the TUI** — duplicates freshness logic already owned by
  `org_files_mtime_signature`. Lost.
- **Supersede SPEC-0129 wholesale** — wrong; its poll-off-thread decision remains correct.

## Acceptance criteria

- [x] Two consecutive `load_tasks(cfg)` with an unchanged corpus return equal task ids/counts
      and the second call does not re-enter orgparse (path-open counter).
- [x] After bumping an org file's mtime (or rewriting it), the next `load_tasks` returns
      updated content / a new parse.
- [x] `invalidate_tasks_cache()` forces the next call to re-parse even if the signature is
      unchanged.
- [x] Desk `reload` from `_reload_async` does not block the event loop for the duration of a
      slow `load_rows` (`test_manual_reload_does_not_block_the_event_loop`).
- [x] Existing SPEC-0128/0129 resilience tests still pass.
- [x] Targeted suite passes (`tests/test_org.py`, `tests/test_tui_resilience.py`, related TUI
      tests). Full `uv run pytest`: 1125 passed; 3 pre-existing failures unrelated to this
      change (`test_idea_state_color` hue spans, `test_columns_env_var_controls_width_when_piped`
      — reproduce on clean tree without these edits).

## Test plan

- **Automated tests:**
  - `tests/test_org.py`: cache hit, miss on mtime rewrite, miss on keyword change,
    `invalidate_tasks_cache`.
  - `tests/test_tui_resilience.py`: `test_manual_reload_does_not_block_the_event_loop`,
    `test_overlapping_reload_async_coalesces` (plus existing SPEC-0128/0129 cases).
- **Manual verification:** Measured on live corpus after the change:
  - `load_rows` cold ≈ 0.78s; **warm ≈ 31ms** (was ~740ms every call).
  - `show_detail` path (resolve + load_detail) ≈ **3.9ms/key** for 10 ids (was ~700ms/key).
  - `resolve_selector` ×10 warm ≈ **10.5ms** (was ~7.4s).
- **Regression guard:** `python3 tools/spec_lint.py` exits 0; ledger regenerated.

## Clock Log

Prefer `wt idea clock-in` / `clock-out` on IDEA-288 (this session).

## Rollout / migration

No data migration. Cache is process-local and transparent. Keyword changes and mtime bumps
miss naturally; tests may call `invalidate_tasks_cache()`.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass for this change; manual timing noted above.
- [x] No regressions attributable to this change.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_(none)_
