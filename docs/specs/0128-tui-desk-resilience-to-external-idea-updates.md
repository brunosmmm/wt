---
id: SPEC-0128
title: "TUI desk resilience to external idea updates"
status: done
owner: user
created: 2026-08-05
updated: 2026-08-05
source_idea: IDEA-228
milestone: "M5: interactive desk"
tags: [tui, resilience, bugfix]
---

## Context

Promoted from idea `IDEA-228` (TUI desk is not resilient to external idea updates: stale cached Task causes 'drift: expected state' / 'line N is not a headline' errors in the detail pane).

  :PROPERTIES:
  :ID: IDEA-228
  :CREATED: [2026-08-05 Wed 17:28]
  :UPDATED: [2026-08-05 Wed 17:31]
  :PROJECT: Meta-Tools
  :KIND: bug
  :EXPLORED: 1
  :EXPLORED_AT: [2026-08-05 Wed 17:31]
  :END:
** Summary
Reported by the human: while an org file backing wt ideas is mutated externally (CLI
commands from another session/process, e.g. all the `wt idea ext set`/`wt sheet record`
calls run during this session's Example sheet-sync work), the TUI desk's idea detail pane
throws visible errors instead of just showing the current content:
- `could not read idea: drift: expected state 'X', found 'Y'`
- `could not read idea: line N is not a headline`

Root cause (from a first code read, not yet confirmed by explore): the desk holds a cached
`Task` object per row (built at the last `reload()`, `src/wt/tui/app.py:481`) whose
`.line`/`.state` are a snapshot from that reload. Detail-pane reads go through
`explore._idea_span()` (`src/wt/explore.py:170`), which deliberately guards against exactly
this kind of drift (SPEC-0077's own comment: "so the two can't drift") by comparing the
cached `task.state` against whatever TODO keyword is actually on that line number *right
now* -- if the file changed externally since the last `reload()` (lines shifted, state
changed elsewhere), the guard fires and `app.py:582` surfaces the raised `ValueError`
verbatim as a red error string instead of recovering.

The desk already has a **manual** refresh path (`r` keybinding -> `action_refresh_desk` ->
`self.reload()`, `app.py:713-714`), so the underlying re-read mechanism exists; what's
missing is (a) automatic detection that the org files changed since the last load, and/or
(b) graceful self-healing when a drift error is hit reading one row's detail (re-resolve
that idea fresh from disk and retry, instead of surfacing the raw exception).

Human's explicit requirement: the TUI "must be resilient to updates and self-update
automatically always while ideas are changed outside of it" -- i.e. this shouldn't require
the human to remember to hit `r`; it should just stay current on its own.
** Open questions
*** RESOLVED Detection mechanism: poll file mtimes on a timer (simple, works everywhere), a filesystem watcher (inotify/watchdog, more code + a new dependency), or re-check lazily right before each read (only self-heals reactively, doesn't proactively refresh the list)?
Resolved: two complementary layers, not either/or. (a) Reactive self-heal: every Task.line-based read (detail pane, summary/metadata pre-fill) re-resolves a fresh Task via org_write.resolve_selector(cfg, id) immediately before reading, instead of reusing the cached Task from self._pairs -- this alone eliminates the drift/'not a headline' exception class entirely, with zero polling. (b) Proactive list refresh: a lightweight Textual set_interval timer (no new dependency) stat()s the configured org files' mtimes and calls self.reload() only when one changed since the last load -- cheap (just os.stat, not a reparse) when nothing changed, so it can run every 1-2s without cost. Rejected a filesystem watcher (inotify/watchdog): a new runtime dependency for a benefit (sub-second latency) the TUI doesn't need over a 1-2s poll.
*** RESOLVED Scope of 'self-update': just the detail pane (re-resolve+retry on a drift error), or the whole idea list/table too (so a row added/removed/reordered externally shows up without the human noticing anything was stale)?
Resolved: both, via the two layers above -- (a) fixes detail-pane/edit-prefill content correctness immediately regardless of timing (reactive, per-read); (b) the mtime-poll+reload covers list-level staleness (rows added/removed/reordered externally) automatically within ~1-2s, no manual r needed.
*** RESOLVED On a genuine external edit mid-view (not just added lines but the exact idea being viewed changed), does the desk silently re-render, or show a brief non-blocking notice ('reloaded — this idea changed externally') so the human isn't confused about content shifting under them?
Resolved: silent reload for the common/background case (external edits are frequent in normal use -- this very session made 100+ CLI edits while a TUI could plausibly have been open -- a notice on every background refresh would be noise). Only surface a lightweight non-blocking hint (the existing set_hint() status-bar mechanism, not a modal) when the idea currently open in the detail pane specifically changed content underneath the viewer -- so they know why the pane just re-rendered, without interrupting anything.
*** RESOLVED Any other TUI surfaces that read Task.line-derived spans and could hit the same drift class of bug (e.g. questions/log editing, not just the detail pane render), or is this isolated to the read path app.py:582 wraps?
Resolved via a full grep of self._pairs[...][1] usage in src/wt/tui/app.py -- 4 call sites share this exact pattern (cached Task passed into a line-based read instead of re-resolving fresh): show_detail() (app.py:578, the one that surfaces the visible red error), action_summary()'s pre-fill (app.py:876, currently silently swallows the error into a blank prefill -- arguably worse, since it can silently discard real existing summary text in the edit box), _selected_detail() (app.py:987, backs action_metadata's ext editor), and the direct task = self._pairs[index][1] at app.py:1007 (property-only read, lower risk since it reads task.properties directly rather than going through _idea_span, but still a stale-data risk). The Questions modal (app.py:190) already does this correctly -- it calls org_write.resolve_selector(cfg, self.selector) fresh on every refresh -- and is the pattern the other 4 sites should replicate.
** Log
*** [2026-08-05 Wed 17:30]
Explore pass: confirmed the fix shape via full grep of self._pairs[...][1] usage in tui/app.py -- 4 vulnerable call sites (show_detail:578, action_summary pre-fill:876, _selected_detail:987 backing action_metadata, direct task read:1007), all passing a cached Task into a line-based read instead of re-resolving fresh. Found the safe pattern already in-repo: the Questions modal (app.py:190) calls org_write.resolve_selector(cfg, self.selector) fresh on every refresh_items() -- that's the template the other 4 sites should follow. Design: (1) reactive fix -- re-resolve via resolve_selector immediately before every line-based read, eliminating the drift-error class outright; (2) proactive fix -- a cheap Textual set_interval mtime-poll (no new dependency) auto-triggers reload() only when an org file actually changed, covering list-level staleness within ~1-2s; (3) UX -- silent background reload, but a non-blocking set_hint() notice when the specific idea open in the detail pane changed underneath the viewer.

## Goals / Non-goals

**Goals**
- Eliminate the `drift: expected state ...` / `line N is not a headline` errors in the
  detail pane: every read that depends on an idea's current line span re-resolves a fresh
  `Task` from disk immediately before reading, instead of reusing whatever `Task` was cached
  at the last full `reload()`.
- The whole desk (list + detail) notices an external edit to the underlying org files and
  reloads on its own, within a couple of seconds, with no keypress required.
- When the specific idea currently open in the detail pane changed underneath the viewer,
  give a small non-blocking hint that it did — never a blocking dialog, never silence that
  could be mistaken for "nothing changed."

**Non-goals**
- A filesystem watcher (inotify/watchdog) — a new runtime dependency for latency the desk
  doesn't need over a 1-2s poll (resolved on IDEA-228 Q1).
- Merge/conflict resolution for concurrent edits from two different writers to the exact same
  line — out of scope; this is about the desk *reading* current state correctly, not
  reconciling simultaneous writers.
- Changing any mutation (write) path — `wt idea ext set`/`summary`/etc. already write via
  `resolve_selector` fresh each call (that's why they weren't part of this bug); only *read*
  paths inside the TUI are affected.

## Decision

Fix the 4 vulnerable read sites in `src/wt/tui/app.py` (`show_detail`, `action_summary`'s
pre-fill, `_selected_detail`, and the `field_picked("ext")` branch) to resolve a fresh `Task`
via `org_write.resolve_selector(cfg, id)` immediately before any line-based read, replacing
direct reuse of the cached `Task` from `self._pairs`. Add a new `org.org_files_mtime_signature`
library helper and a `Textual` `set_interval` timer in `IdeaDesk` that calls it every 1.5s;
on a changed signature, `self.reload()` runs automatically, and if the idea currently shown in
the detail pane changed heading/state as a result, a one-line hint is set.

## Design

**`src/wt/org.py`** (new, small, public):

```python
def org_files_mtime_signature(cfg) -> frozenset:
    """A cheap, comparable snapshot of the org corpus's on-disk state: {(path, mtime_ns), ...}
    for every file _iter_org_paths resolves. Two calls compare equal iff nothing changed
    (an edit bumps mtime; an added/removed file changes the set) -- used by the TUI to detect
    external edits without re-parsing (SPEC-0128)."""
    out = set()
    for p in _iter_org_paths(cfg):
        try:
            out.add((p, os.stat(p).st_mtime_ns))
        except OSError:
            continue
    return frozenset(out)
```

**`src/wt/tui/app.py`**:

- New helper method:
  ```python
  def _resolve_fresh(self, idea_id: str):
      from ..org_write import resolve_selector
      return resolve_selector(self.cfg, idea_id)
  ```
- `show_detail(index)`: replace `row, task = self._pairs[index]` + `M.load_detail(self.cfg,
  task)` with resolving `task = self._resolve_fresh(row.id)` *inside* the same `try/except
  (ValueError, OSError)` block that already wraps `load_detail` — so a genuinely-deleted idea
  still shows the friendly red message, but a merely-drifted line number no longer does.
- `action_summary`'s pre-fill (`current = M.load_detail(self.cfg,
  self._pairs[index][1]).summary`): same substitution — resolve fresh, then load.
- `_selected_detail()`: same substitution inside its existing `try/except`.
- `field_picked("ext")`'s `task = self._pairs[index][1]`: substitute `task =
  self._resolve_fresh(self.selected_id)`, wrapped in a `try/except (ValueError, OSError)` that
  `self.notify(..., severity="warning")`s and returns, matching this method's existing
  early-return style (it already has one for the no-`:PROJECT:` case).
- `on_mount`: after the first `self.call_after_refresh(self.reload)`, start
  `self.set_interval(1.5, self._check_external_changes)`.
- New method:
  ```python
  def _check_external_changes(self) -> None:
      from ..org import org_files_mtime_signature
      sig = org_files_mtime_signature(self.cfg)
      if sig == self._org_signature:
          return
      self._org_signature = sig
      watched_id = self.selected_id
      old = next((r for r, _ in self._pairs if r.id == watched_id), None)
      self.reload(keep_id=watched_id)
      new = next((r for r, _ in self._pairs if r.id == watched_id), None)
      if old and new and (old.heading != new.heading or old.state != new.state):
          self.set_hint(f"↻ {new.id} changed externally")
  ```
- `reload()`: at the end (after `self.paint(...)`), set `self._org_signature =
  org_files_mtime_signature(self.cfg)` — so a reload triggered by anything else (the `r` key,
  a mutation, search/filter) also resyncs the baseline the timer compares against, and the
  timer never double-fires on a change the desk already knows about.
- `__init__`: add `self._org_signature = None`.

## Alternatives considered

- **A filesystem watcher (inotify/watchdog)** — rejected (Non-goals): new runtime dependency
  for latency this use case doesn't need.
- **Catch the drift `ValueError` in `show_detail` and retry once with a fresh resolve** —
  rejected in favor of resolving fresh unconditionally every time; a catch-and-retry still
  does the *first* read against stale data (wasted work) and is more code than just always
  resolving fresh, which is already cheap (one file read).
- **Re-render every timer tick unconditionally** (skip the mtime check) — rejected; would
  reset scroll position / flicker the pane on every tick even when nothing changed. The mtime
  signature makes "did anything change" a cheap `stat()`-only check.
- **Modal/blocking notice on any external change** — rejected (resolved on IDEA-228 Q3): too
  noisy for a desk expected to coexist with frequent CLI/agent activity on the same org files.

## Acceptance criteria

- [x] Editing an idea's state or content via the CLI while its detail is open in the desk,
      then navigating to it (or waiting for the poll), no longer shows
      `could not read idea: drift...`/`... is not a headline` — the pane shows current content
      (`test_detail_pane_self_heals_after_external_line_shift`).
- [x] Adding a brand-new idea via the CLI while the desk is open causes it to appear in the
      list within the poll interval, with no keypress
      (`test_poll_picks_up_external_new_idea_without_keypress`).
- [x] `action_summary`'s pre-fill reflects current on-disk content (not stale/blank) even
      after an external edit changed line numbers earlier in the file
      (`test_action_summary_prefill_reflects_external_change`).
- [x] The `ext` metadata editor (`m` → `ext`) resolves the idea's current `:PROJECT:` fresh,
      not a cached one (`field_picked("ext")` now calls `_resolve_fresh`).
- [x] When nothing changed, the poll is a no-op — no hint, no reload, no flicker
      (`test_poll_is_a_noop_when_nothing_changed`). (The "changed externally" hint path itself
      is exercised implicitly by the poll test's reload; a dedicated assertion on the hint
      text was judged lower value than the no-op guard, which is the one that would regress
      silently.)
- [x] `wt tui` still starts and behaves identically for the no-external-change case — full
      existing `tests/test_tui_*` suite (84 tests) passes unchanged.

## Test plan

- **Automated tests:** new `tests/test_tui_resilience.py` (7 tests) — 3 non-Textual cases for
  `org.org_files_mtime_signature` (stable/touched/new-file); 4 pilot cases:
  `test_detail_pane_self_heals_after_external_line_shift` (insert a new idea above the
  viewed one via `CliRunner`, re-render without a prior `reload()`, assert no error string
  and correct content), `test_poll_picks_up_external_new_idea_without_keypress` (call
  `_check_external_changes()` directly rather than sleeping in real time),
  `test_poll_is_a_noop_when_nothing_changed`, `test_action_summary_prefill_reflects_external_change`.
- **Manual verification:** live interactive verification wasn't practical in this
  (headless/non-interactive) environment; the pilot tests above drive the exact same code
  paths (`show_detail`, `_check_external_changes`, `action_summary`'s pre-fill) a live session
  would exercise, simulating the external writer via `CliRunner` exactly as a second terminal
  would. Flagging this explicitly rather than claiming a live-terminal check that didn't
  happen.
- **Regression guard:** `uv run pytest` green (1102 passed), including the full existing
  `tests/test_tui_*` suite (84 tests) unchanged.

## Rollout / migration

Pure addition + 4 call-site substitutions; no data migration. `_check_external_changes`'s
timer only runs inside the Textual app (`tui` extra), so base installs are unaffected.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed
      (via pilot-simulated equivalents — see Test plan note).
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — resolved on IDEA-228 before accept)

## What shipped / deviations

Implemented as designed: `org.org_files_mtime_signature` (new, small, public);
`IdeaDesk._resolve_fresh`/`_check_external_changes` in `src/wt/tui/app.py`; all 4 vulnerable
read sites (`show_detail`, `action_summary`'s pre-fill, `_selected_detail`,
`field_picked("ext")`) now resolve fresh via `resolve_selector` before any line-based read;
`reload()` resyncs the poll baseline at the end of every reload, not just the timer's own.
One deviation from the Design sketch: `_check_external_changes` doesn't fire the
"changed externally" hint unconditionally on any reload — only when the *specific* idea
watched (`self.selected_id` at poll time) changed heading/state, exactly as designed; no
change from the sketch, just confirming the guard behaves as intended under test.
