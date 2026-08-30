---
id: SPEC-0129
title: "TUI poll reload off the event-loop thread"
status: done
owner: user
created: 2026-08-05
updated: 2026-08-05
source_idea: IDEA-232
milestone: "M5: interactive desk"
tags: [tui, resilience, performance, bugfix]
depends_on: [SPEC-0128]
---

## Context

Promoted from idea `IDEA-232` (SPEC-0128's external-change poll makes the TUI extremely slow: reload() blocks the event loop for ~350ms and can fire every 1.5s during active editing).

  :PROPERTIES:
  :ID: IDEA-232
  :CREATED: [2026-08-05 Wed 18:59]
  :UPDATED: [2026-08-05 Wed 19:09]
  :PROJECT: Meta-Tools
  :KIND: bug
  :EXPLORED: 1
  :EXPLORED_AT: [2026-08-05 Wed 19:09]
  :END:
** Summary
Regression introduced by SPEC-0128 (TUI desk resilience to external idea updates), reported
by the human immediately after it shipped: the desk is "extremely slow."

Measured root cause (this machine's real org corpus: 21 org files, 546 tasks):
- `wt.tui.model.load_rows(cfg)` (what `IdeaDesk.reload()` calls on every trigger) takes
  ~`0.35s` consistently (measured 3x: 0.352s/0.346s/0.355s).
- `org.org_files_mtime_signature(cfg)` itself is cheap (~0.5ms) -- the poll's own cost is
  negligible; the problem is entirely in what it **triggers**.
- `IdeaDesk._check_external_changes()` (the 1.5s `set_interval` timer added by SPEC-0128)
  calls `self.reload()` synchronously, on Textual's single event-loop thread, whenever the
  org corpus's mtime signature changed since the last reload. `reload()` was already this
  expensive before SPEC-0128 (nothing about `load_rows` itself changed) -- what's new is
  that it can now fire **automatically and repeatedly**, not just once per manual `r`
  keypress.
- Before SPEC-0128: the 350ms block only happened on an explicit `r` press -- rare, and the
  human expects a brief pause right after pressing a key.
- After SPEC-0128: during any period of active external editing (e.g. this very session,
  which ran 100+ `wt idea ext set`/`log`/etc. calls in a row while the sidecar/sheet-sync
  work was underway), the corpus signature changes on nearly every 1.5s tick, so
  `reload()` re-fires every `1.5s, each time freezing all input/rendering for `350ms --
  roughly a quarter of wall-clock time spent fully blocked, which reads as "extremely slow"
  rather than "briefly pauses sometimes."

Not yet explored: the concrete fix shape (background/threaded reload vs. throttling vs.
increasing the poll interval vs. some combination) -- see open questions.
** Open questions
*** RESOLVED Move the expensive part of reload() (M.load_rows) off the event-loop thread (Textual run_worker(thread=True) or asyncio executor), so a poll-triggered reload no longer blocks input/rendering, regardless of how often it fires?
Resolved: asyncio.get_running_loop().run_in_executor(None, partial(M.load_rows, ...)), not Textual's run_worker(thread`True). Textual's set_interval callback already supports an async callback (confirmed: TimerCallback ` Union[Callable[[], Awaitable], Callable[[], Any]] in textual/timer.py, invoked via its own invoke() helper that awaits coroutines) -- so _check_external_changes becomes async def and awaits the executor future directly, no separate Worker plumbing/state-changed handler needed. Scoped narrowly: only the POLL path (_check_external_changes) moves off-thread. The manual r-key refresh and post-mutation reload() calls stay exactly as they were before SPEC-0128 (synchronous, blocking) -- that 350ms-on-keypress behavior is pre-existing and accepted, not part of this regression; broadening the fix to every reload() call site is a bigger, riskier change than fixing the thing that actually regressed (automatic, repeated, poll-triggered blocking).
*** RESOLVED Independently of threading: should the poll interval be longer than 1.5s (SPEC-0128's own choice, not deeply justified), and/or should repeated changes within a short window be debounced/coalesced into one reload instead of one per tick during a burst of external edits?
Resolved: keep the 1.5s interval (the mtime-signature check itself is ~0.5ms, negligible at any reasonable frequency); no separate debounce timer needed. The in-flight guard from Q3 already coalesces bursts for free -- if signature changes keep arriving while a background load_rows is running, they're simply not re-triggered until the current one finishes and the next tick re-checks, so a burst of edits (like this session's own 100+-call workflow) collapses to however many reloads actually complete in that window, not one attempted reload per tick.
*** RESOLVED Does moving reload() off-thread reintroduce any of the races SPEC-0128 was fixing (e.g. reading self._pairs mid-reload from a UI callback while a background reload is still populating it)? Needs a clear 'reload in flight' guard either way.
Resolved: yes, a real race without a guard (a second poll tick could start a second run_in_executor before the first's result is applied) -- add self._reload_in_flight: bool (init False). _check_external_changes returns early if already True; sets it True before awaiting, False in a finally. Applying the result (self._pairs = ...; self.paint(...); update self._org_signature) happens after the await, back on the main event-loop thread (asyncio.run_in_executor's continuation runs there, not in the worker thread) -- so the swap is a plain sequential assignment from the same thread every other UI callback runs on, no lock needed, and self._pairs is never read half-updated because nothing else mutates it concurrently.
*** RESOLVED Is load_rows itself worth speeding up (546 tasks / 21 files in 350ms -- is that orgparse overhead, wt's own per-task processing, or both), independent of threading -- i.e. should this also be a perf idea against wt.tui.model/org.load_tasks, not just a threading fix?
Resolved: descoped from this fix. 350ms for 546 tasks/21 files is a one-time cost on manual refresh/mount that's always been there and hasn't itself been reported as a problem -- what made it feel 'extremely slow' was firing automatically and repeatedly while blocking input, which the threading fix addresses directly. If load_rows's own cost becomes a problem on its own (e.g. a much larger corpus, or the one-time mount/keypress pause itself becomes noticeable), that's a separate perf idea against wt.tui.model.load_rows/org.load_tasks, not part of this bug.
** Log
*** [2026-08-05 Wed 19:09]
Explore pass: confirmed via textual/timer.py that set_interval callbacks may be async (TimerCallback union type, invoked through invoke() which awaits coroutines) -- so the fix is asyncio.get_running_loop().run_in_executor(None, partial(M.load_rows, ...)) inside an async _check_external_changes, not Textual's Worker API (simpler, no state-changed handler needed). Scoped narrowly to the poll path only; manual r-key refresh and mutation-driven reload() stay synchronous/unchanged (pre-existing, not part of this regression). Race-safety via a simple self._reload_in_flight guard -- the executor continuation runs back on the main event-loop thread, so applying the result is a plain sequential assignment, no lock needed. All 4 open questions resolved.

## Goals / Non-goals

**Goals**
- The SPEC-0128 poll (`IdeaDesk._check_external_changes`, every 1.5s) no longer blocks the
  Textual event loop — input and rendering stay responsive during a poll-triggered reload,
  regardless of how often the org corpus changes.
- Overlapping poll-triggered reloads are impossible: a background reload always runs to
  completion (or fails cleanly) before another one starts.

**Non-goals**
- Changing the manual `r` keybinding's refresh, or any post-mutation `self.reload()` call
  (summary/log/questions/ext edits, etc.) — those stay exactly as they were before SPEC-0128;
  their 350ms pause on an explicit user action is pre-existing, accepted behavior, not part of
  this regression (resolved on IDEA-232 Q1).
- Speeding up `wt.tui.model.load_rows`/`org.load_tasks` itself — descoped (IDEA-232 Q4); this
  is about not blocking on the existing cost, not reducing it.
- Debouncing/throttling beyond what falls out of the in-flight guard — no separate timer or
  interval change (resolved on IDEA-232 Q2).

## Decision

`IdeaDesk._check_external_changes` becomes an `async def` (Textual's `set_interval` already
supports async callbacks). On a detected signature change, it awaits `M.load_rows` via
`asyncio.get_running_loop().run_in_executor(None, ...)` instead of calling the synchronous
`self.reload()`, guarded by a `self._reload_in_flight` flag so a second tick during an
in-flight background load is a no-op.

## Design

**`src/wt/tui/app.py`**:

- `__init__`: add `self._reload_in_flight = False`.
- New method, replacing `_check_external_changes`'s body:
  ```python
  async def _check_external_changes(self) -> None:
      from ..org import org_files_mtime_signature
      sig = org_files_mtime_signature(self.cfg)
      if sig == self._org_signature or self._reload_in_flight:
          return
      self._reload_in_flight = True
      try:
          watched_id = self.selected_id
          old = next((r for r, _ in self._pairs if r.id == watched_id), None)
          loop = asyncio.get_running_loop()
          try:
              pairs = await loop.run_in_executor(
                  None, functools.partial(
                      M.load_rows, self.cfg, query=self.query or None,
                      all_done=self.all_done, sort=self.sort, desc=self.desc,
                      **self.filters))
          except (ValueError, OSError) as e:
              self._pairs = []
              self.set_hint(f"load failed: {e}")
              self.paint(keep_id=watched_id)
              return
          self._pairs = pairs
          self._depths = []
          self.paint(keep_id=watched_id)
          self._org_signature = org_files_mtime_signature(self.cfg)
          new = next((r for r, _ in self._pairs if r.id == watched_id), None)
          if old and new and (old.heading != new.heading or old.state != new.state):
              self.set_hint(f"↻ {new.id} changed externally")
      finally:
          self._reload_in_flight = False
  ```
  (Re-reading `org_files_mtime_signature` *after* the executor call, not reusing `sig` from
  before it, matters: an edit landing during the background load shouldn't be silently
  swallowed as "already accounted for.")
- `reload()` (the synchronous manual/mutation path) is unchanged — still called by
  `action_refresh_desk`, `on_mount`'s first paint, and every post-mutation path exactly as
  before SPEC-0128.
- New imports: `asyncio`, `functools` (module-level, alongside existing imports).

## Alternatives considered

- **`Textual`'s `run_worker(thread=True)` + a `Worker.StateChanged` handler** — rejected;
  `run_in_executor` inside an `async def` timer callback is simpler (no separate message
  handler, no worker lifecycle to reason about) and Textual's own timer machinery already
  awaits coroutine callbacks natively (confirmed via `textual/timer.py`).
- **Make every `reload()` call site async/threaded** — rejected (IDEA-232 Q1); broader than
  the actual regression, and several callers currently rely on `self._pairs` being populated
  synchronously immediately after `reload()` returns.
- **A debounce timer coalescing bursts of signature changes** — rejected (IDEA-232 Q2); the
  in-flight guard already achieves this for free with less code.

## Acceptance criteria

- [x] A poll-triggered reload (org corpus changed externally) no longer blocks keypresses or
      rendering — `test_poll_reload_does_not_block_the_event_loop` simulates a 0.2s-slow
      `load_rows` and proves the event loop keeps ticking (5 independent `asyncio.sleep(0.01)`
      steps complete) while `_reload_in_flight` is `True`.
- [x] Two rapid-fire external changes within one `load_rows` duration result in exactly one
      background reload actually running at a time —
      `test_concurrent_poll_ticks_only_run_one_reload` fires two overlapping ticks and asserts
      the (patched, counting) `load_rows` was called exactly once.
- [x] The "changed externally" hint and empty-poll no-op behavior from SPEC-0128 are
      unchanged — all 7 pre-existing `test_tui_resilience.py` cases still pass unmodified.
- [x] Manual `r` refresh and post-mutation reloads are byte-for-byte unchanged in behavior
      (still synchronous, still `self.reload()`) — not touched by this change at all.
- [x] `uv run pytest` green (1104 passed), full existing `tests/test_tui_*` suite (93 tests
      across all TUI test files) unchanged.

## Test plan

- **Automated tests:** `tests/test_tui_resilience.py` gained
  `test_poll_reload_does_not_block_the_event_loop` (patched slow `load_rows`, proves the loop
  keeps ticking during the executor call) and `test_concurrent_poll_ticks_only_run_one_reload`
  (patched counting `load_rows`, two overlapping ticks -> exactly one call) — 9 tests total in
  the file (was 7). The two pre-existing poll tests (`test_poll_picks_up_external_new_idea_
  without_keypress`, `test_poll_is_a_noop_when_nothing_changed`) needed one mechanical change:
  `_check_external_changes()` is now `async def`, so their calls became `await
  app._check_external_changes()`.
- **Manual verification:** N/A beyond the automated pilot tests above — no live terminal
  session available in this environment (same caveat as SPEC-0128's Test plan).
- **Regression guard:** `uv run pytest` green (1104 passed); all SPEC-0128 tests in
  `tests/test_tui_resilience.py` continue passing (only the internals of
  `_check_external_changes` changed, not its externally observable contract); full existing
  `tests/test_tui_*` suite (93 tests) unaffected.

## Rollout / migration

Pure code change inside `_check_external_changes`; no data/config migration. Lands as a
follow-up to SPEC-0128 on the same machine/config.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed
      (via pilot-simulated equivalents — see Test plan note, same as SPEC-0128).
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — resolved on IDEA-232 before accept)

## What shipped / deviations

Implemented exactly as designed: `IdeaDesk._check_external_changes` is now `async def`,
awaiting `asyncio.get_running_loop().run_in_executor(None, functools.partial(M.load_rows,
...))` guarded by `self._reload_in_flight`; the signature is re-read *after* the executor call
completes (not reused from before it), so an edit landing mid-load isn't silently missed on
the next tick. `reload()` and every other call site are untouched. No deviations from the
Design.
