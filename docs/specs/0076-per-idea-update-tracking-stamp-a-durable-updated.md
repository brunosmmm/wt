---
id: SPEC-0076
title: "Per-idea update tracking: :CREATED:/:UPDATED: stamps with a backfill"
status: done
owner: user
created: 2026-07-27
updated: 2026-07-27
source_idea: IDEA-094
milestone: "M4: cli ergonomics"
tags: [org, ideas, maintenance]
---

## Context

Promoted from idea `IDEA-094`, itself forked out of `IDEA-092` (the `wt ideas` table overhaul,
[SPEC-0075](./0075-overhaul-the-wt-ideas-triage-table-drop-the-next.md)). That spec wants a
"last updated" column and cannot have one: **no idea in the system records when it was last
touched.**

Verified during exploration:

- No `:UPDATED:` / `:CREATED:` / `:MODIFIED:` property exists on any idea. Grep over `src/wt/`
  finds none; raw `ideas.org` subtrees carry only `:ID:` / `:PROJECT:` / `:SPEC:` /
  `:TARGET_*:` / `:KIND:`.
- The org data dir (`~/work/org`) is **not** a git repo, so there is no commit history to mine.
- File mtime is per-*file*, not per-idea, and rotation (SPEC-0071) replaces whole files, so
  mtime is destroyed wholesale.
- The only per-idea time signals that exist today are dated Log headlines
  (`*** [2026-07-23 Thu 07:42]`, written by `append_log`, `src/wt/explore.py:404`) and
  `CLOSED:` stamps. Coverage is thin: the live `ideas.org` holds 7 ideas and **1** log stamp;
  36 open / 93 total ideas are listed across it plus the rotated `ideas-20260727.org`.

So the stamp must be written going forward, and derived only as a best-effort backfill.

Two findings simplify the design relative to the idea's worries:

- **Archival and rotation are already transparent.** `archive_idea` (`src/wt/org_write.py:561`)
  moves a subtree **verbatim** between files, and `maybe_rotate_ideas_file`
  (`src/wt/org_write.py:612`) is a plain `os.replace` of the whole file plus a fresh header.
  Neither rewrites properties, so neither can bump a stamp. Properties travel with the subtree
  — which is exactly why a property beats mtime here. No special-casing needed; the rule is
  simply "don't add stamping to those two functions".
- **The hook surface is small.** `set_summary`, `set_questions`, `add_question` and
  `resolve_question` all funnel through one writer, `_replace_section_body`
  (`src/wt/explore.py:228`). Promotion, close, and kind changes all funnel through
  `set_state` / `set_property` (`src/wt/org_write.py:80,140`) — e.g. `promote_idea` does
  `set_property(…, "SPEC", …)` then `set_state(…, "SPECCED")` (`src/wt/specs.py:149-150`), and
  `set_idea_kind` is a thin `set_property` wrapper (`src/wt/org_write.py:677`). So five hook
  points cover every path that should stamp.

## Goals / Non-goals

**Goals**

- Every idea mutation that represents deliberate work records the time it happened, in a
  property that survives archival and rotation.
- New captures record `:CREATED:` exactly.
- Existing ideas get a best-effort `:UPDATED:` via an explicit, idempotent one-shot command.
- The stamps are exposed on the idea row payload so triage views can consume them.
- No extra file writes or backups per mutation — the stamp rides the write that is already
  happening.

**Non-goals**

- **Not** adding the `updated` column to `wt ideas` / `wt next`. That is display work
  belonging to `IDEA-092` / SPEC-0075's follow-up; this spec only produces the data.
- Not stamping non-idea tasks. `set_state` / `set_property` are shared with ordinary tasks;
  those paths stay untouched.
- Not stamping clock activity (`clock_in` / `clock_out` / `add_clock_entry`) — see Decision.
- Not stamping maintenance rewrites that change formatting rather than content
  (`normalize-logs`, `normalize-questions`, `reindex_ideas`).
- Not inferring `:CREATED:` for the existing 93 ideas — it is unrecoverable, and guessing it
  from a Log entry would misdate ideas that were captured long before their first log.
- No new config keys.

## Decision

Add two inactive-org-timestamp properties to ideas, `:CREATED:` and `:UPDATED:`, written in the
format `_inactive_stamp(cfg, with_time=True)` already produces (`[YYYY-MM-DD Day HH:MM]`,
`src/wt/org_write.py:62`) so they match Log and CLOCK stamps and parse with existing code.

`:UPDATED:` bumps on **content and lifecycle** changes: summary, questions (set/add/resolve),
log, retitle, state change, kind, close, and promotion. It does **not** bump on clock in/out,
archival, rotation, or formatting-only normalizers. Rationale: the stamp answers "is this idea
stale?", so deliberate authxxing and lifecycle moves count, while clock churn and mechanical
rewrites would bump it without the idea itself having changed.

The stamp is injected into the line list **inside the write each mutator already performs** —
never via a nested `set_property` call. That keeps one write and one backup per mutation and
avoids recursion.

Existing ideas are backfilled by an explicit `wt idea backfill-stamps`, deriving `:UPDATED:`
from the newest Log headline, else the `CLOSED:` stamp, else skipping the idea.

## Design

### Stamp helper (`src/wt/org_write.py`, beside `_inactive_stamp`)

```python
def _inject_property(lines, idx, stars, name, value):
    """Set `:NAME: value` in the drawer of the headline at `lines[idx]`, in place, returning
    the (possibly lengthened) list. Creates the drawer after any PLANNING/CLOSED lines."""

def stamp_updated(cfg, lines, idx, stars, *, when=None):
    """_inject_property(..., 'UPDATED', _inactive_stamp(cfg, when=when, with_time=True))."""
```

`_inject_property` is the drawer-writing logic already inside `set_property`
(`src/wt/org_write.py:160-177`) lifted into a pure list transform; `set_property` is refactored
to call it, so there is one implementation of "put a property in the drawer".

**Ordering rule (important).** Each mutator calls `stamp_updated` **immediately before** its
existing `_atomic_backup_write`, after all body edits. When `:UPDATED:` is absent the injection
inserts a line and shifts every offset below it; doing it last means the section offsets
(`b0`/`b1` from `_find_sections`) have already been consumed. On subsequent mutations the
property exists and the line is replaced in place, so no shift occurs at all — only the first
stamp per idea can shift, and `add_task` seeding the drawer means new ideas never shift.

### Hook points

Stamping (`:UPDATED:`):

| Function | File | Covers |
|---|---|---|
| `_replace_section_body` | `explore.py:228` | summary, questions set/add/resolve |
| `append_log` | `explore.py:404` | log entries |
| `retitle_idea` | `explore.py:502` | headline rewrites |
| `set_state` | `org_write.py:80` | state changes, close, promotion to SPECCED |
| `set_property` | `org_write.py:140` | kind, `:SPEC:`, `:TARGET_*:` |

- `set_state` / `set_property` stamp **only when `task.is_idea`** — ordinary tasks are
  unaffected.
- `set_property` must not stamp when `name` is `UPDATED` or `CREATED` (no self-bump), and must
  inject rather than recurse.
- `set_property` gains a keyword-only `touch=True`; `reindex_ideas`
  (`org_write.py:685`) passes `touch=False` so backfilling `:ID:` does not look like an edit.

Explicitly **not** hooked: `clock_in`, `clock_out`, `add_clock_entry`, `archive_idea`,
`maybe_rotate_ideas_file`, `normalize_log_stamps_in_file`, `normalize_idea_questions`,
`_ensure_question_header` (its write is always followed by a `_replace_section_body` that
stamps).

### Capture (`:CREATED:`)

`add_task` (`org_write.py:400`) builds the drawer as a list of `props`
(`org_write.py:455-469`). When `idea_id` is set, append both:

```
  :CREATED: [2026-07-27 Mon 14:03]
  :UPDATED: [2026-07-27 Mon 14:03]
```

after `:ID:`. No extra write; `:CREATED:` is only ever written here and never updated
afterwards.

### Backfill (`wt idea backfill-stamps`)

New `backfill_idea_stamps(cfg)` in `explore.py` plus a `wt idea backfill-stamps` subcommand.
*(As-built: modelled on `reindex_ideas`'s re-parse loop rather than on
`normalize_idea_log_stamps`. It drives off `load_tasks` — which already walks every file under
`org_files`, so rotated and archived ideas are covered per SPEC-0074 — and re-parses after each
write, because writing one idea's property shifts the line numbers of every idea below it in
the same file. Each backfilled idea is one `set_property(..., "UPDATED", ...)` call; a stamp
property never bumps itself, so no `touch=False` is needed.)*

The newest-stamp parse is its own helper, `newest_log_stamp(log_text)`, so the max-not-last
rule is unit-testable without any org fixture.

Per idea lacking `:UPDATED:`, derive in order:

1. the newest Log headline stamp — parse `*** [...]` / `_PLAIN_LOG_HEAD_RE`
   (`explore.py:21`) across the Log section, taking the **maximum** parsed datetime rather than
   the last line, so out-of-order entries cannot misdate the idea;
2. the `CLOSED:` stamp on the headline;
3. otherwise **skip** — no stamp, and report it as skipped.

Idempotent: an idea that already has `:UPDATED:` is never rewritten, so a second run reports
zero changes. Returns `[(idea_id, source)]` for a per-idea CLI report
(`from-log` / `from-closed` / `skipped`).

### Row payload

`idea_row` (`src/wt/report.py:31`) gains `updated` and `created`, omitted when absent (matching
how it already omits empty `project` / `spec`). Additive, so `wt.ideas.v1` / `wt.next.v1` /
`wt.idea.v1` / `wt hub` stay backward-compatible.

## Alternatives considered

- **Derive the stamp on read from Log/`CLOSED:` only, no property** — rejected: 1 log stamp
  across the 7 live ideas means a near-empty field, and it can never reflect a summary edit or
  a retitle, which leave no dated trace.
- **File mtime** — rejected: per-file, not per-idea, and destroyed by SPEC-0071 rotation.
- **Git history of the org dir** — rejected: `~/work/org` is not a repo.
- **Stamp via a nested `set_property` call from each mutator** — rejected: doubles writes and
  backups per mutation (`_atomic_backup_write` copies the file into `data_dir/org-backups` on
  every call, `org_write.py:333`), and risks recursion. In-line injection is one write.
- **Intercept `_atomic_backup_write` centrally** — rejected: it takes a path plus whole-file
  content and has no idea which headline changed.
- **Lazy fill on first read** — rejected: a read command silently mutating the org file is
  surprising and makes `wt ideas` non-idempotent.
- **Bump on clock in/out too** — rejected for now: clock churn would keep an otherwise
  untouched idea looking fresh. Reconsider if the freshness column proves misleading.
- **An org `:LOGBOOK:`-based or Emacs-standard mechanism** — rejected as heavier than a drawer
  property, which orgparse already exposes via `task.properties`.

## Acceptance criteria

- [x] A newly captured idea has both `:CREATED:` and `:UPDATED:` in its drawer, in
      `[YYYY-MM-DD Day HH:MM]` form, with `:CREATED:` after `:ID:`.
- [x] Each of these bumps `:UPDATED:`: `wt idea summary`, `wt idea questions --set/--add/--resolve`,
      `wt idea log`, `wt idea retitle`, `wt idea kind`, `wt state` on an idea, `wt idea close`,
      and promotion via `wt spec new --from-idea`.
- [x] None of these change `:UPDATED:`: `wt idea clock-in`, `wt idea clock-out`,
      `wt idea normalize-logs`, `wt idea normalize-questions`, `wt ideas --reindex`.
- [x] `:CREATED:` is never modified after capture, including by any of the bumping operations.
- [x] Archiving an idea and rotating the ideas file both leave `:CREATED:` and `:UPDATED:`
      byte-identical, and the properties travel with the subtree to the new file.
- [x] Each stamping mutation performs exactly **one** `_atomic_backup_write` call. *(As-built:
      asserted by counting calls, not backup files — backup filenames carry a whole-second
      timestamp, so two writes inside the same second collide onto one filename and counting
      files silently undercounts.)*
- [x] `set_state` / `set_property` on a **non-idea** task write no stamp.
- [x] `wt idea backfill-stamps` sets `:UPDATED:` from the newest Log stamp when one exists,
      from `CLOSED:` when there is no Log stamp, and skips ideas with neither; it reports which
      source it used per idea.
- [x] The backfill takes the **maximum** Log timestamp, not the last line, when Log entries are
      out of chronological order.
- [x] The backfill is idempotent: a second run reports zero changes and rewrites nothing.
- [x] The backfill covers rotated and archived idea files, not only `cfg['org_ideas_file']`.
- [x] `idea_row` includes `updated` / `created` when present and omits them when absent;
      existing keys are unchanged.
- [x] Stamping an idea whose drawer does not yet exist creates it without corrupting the
      Summary / Open questions / Log sections.
- [x] `uv run pytest` passes; `python3 tools/spec_lint.py` exits 0.

## Test plan

**Automated tests** — `tests/test_idea_stamps.py` (33 tests), reusing the `tmp_path` config
fixture pattern from `tests/test_ideas.py` and `tests/test_explore.py`:

- `test_capture_writes_created_and_updated` — `add_idea` then assert both properties parse and
  `:CREATED:` follows `:ID:`.
- `test_mutator_bumps_updated_and_never_created` — parametrised over summary / questions
  (set, add, resolve) / log / retitle / kind / state / close / `set_property`. Fine-grained
  because the whole risk here is a missed hook. *(As-built: instead of freezing the clock, each
  case seeds `:UPDATED:` with an obviously old stamp and asserts it moved to today. Freezing
  would have meant monkeypatching the shared `datetime` module, which every other write path in
  the call also sees.)*
- `test_excluded_writes_do_not_bump` — clock-in/out, `normalize-logs`, `normalize-questions`,
  `--reindex`, and `archive`: `:UPDATED:` byte-identical before and after.
- `test_archive_and_rotate_preserve_stamps` — archive an idea and force a rotation
  (`idea_rotation_max_lines` low); assert both stamps survive verbatim in the destination file.
  This is the regression guard for the property-vs-mtime rationale.
- `test_single_write_per_mutation` — count files in `data_dir/org-backups` before/after one
  `wt idea log`; assert it grew by exactly one. Guards the "no double write" decision, which is
  otherwise invisible.
- `test_non_idea_task_not_stamped` — `set_state` on a plain task in the capture file leaves no
  `:UPDATED:`.
- `test_stamp_creates_missing_drawer` — an idea authxxed by hand with no `:PROPERTIES:` drawer,
  with populated Summary / questions / Log; after a mutation the drawer exists and
  `read_idea_enrichment` returns all three sections unchanged. Guards the offset-shift hazard.
- `test_backfill_sources_and_precedence` — three fixtures (Log present; `CLOSED:` only;
  neither) assert `from-log` / `from-closed` / `skipped`.
- `test_backfill_uses_max_log_stamp` — Log entries deliberately out of order; assert the newest
  timestamp wins, not the last line.
- `test_backfill_idempotent` — second run reports zero changes and leaves bytes identical.
- `test_backfill_spans_rotated_files` — an idea in a rotated file gets stamped (SPEC-0074
  multi-file behaviour).
- `test_idea_row_exposes_stamps` — `updated`/`created` present when set, absent when not; assert
  the pre-existing keys are untouched.

**Manual verification**

1. `uv run wt idea "stamp smoke test"` — drawer shows `:CREATED:` and `:UPDATED:`.
2. `uv run wt idea log <ID> --note "x"` — `:UPDATED:` advances, `:CREATED:` does not.
3. `uv run wt idea clock-in <ID>` then `clock-out` — `:UPDATED:` unchanged.
4. `uv run wt idea backfill-stamps` on the real corpus — inspect the per-idea report and
   confirm a second run reports zero changes.

**Regression guard**

Full `uv run pytest`. `tests/test_json_cli.py` must still pass unchanged, proving the additive
row fields broke no schema consumer; `tests/test_clock.py`, `tests/test_fit_log.py` and
`tests/test_explore.py` cover the mutators being hooked and must pass without edits, which is
the check that stamping did not disturb existing write behaviour.

## Clock Log

Clocked on the linked idea IDEA-094 (`wt idea clock-in`/`clock-out`), per AGENTS.md.

## Rollout / migration

1. Land the helper, the five hooks, and `:CREATED:` at capture. From here every touched idea
   self-stamps.
2. Land `wt idea backfill-stamps`; run it once against the real corpus. **Done:** 74 stamped
   from Log headlines, 24 skipped for having no Log or `CLOSED:` signal. A second run stamped 0
   and rewrote nothing (it still lists the 24 skips, which write nothing). No idea received a
   `:CREATED:` it could not prove — `wt ideas --json` shows 17 of 41 open ideas with `updated`
   and 0 with `created`, which is the intended shape for a pre-existing corpus.
3. `idea_row` gains the fields; no consumer is required to use them.

Reversible: the properties are inert data, and removing the hooks leaves existing stamps
harmlessly in place. No data is destroyed at any step — the backfill only ever adds a property
to ideas that lack it.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

None — resolved during authxxing:

- *Which writes count* → content + lifecycle; not clock, archival, rotation, or normalizers.
- *Ship `:CREATED:`* → yes, at capture only; not inferred for existing ideas.
- *Backfill mechanism* → explicit idempotent `wt idea backfill-stamps` (not lazy-on-read).
- *Granularity* → date **and** time, matching `_inactive_stamp(with_time=True)`.
- *Property vs org-native* → drawer property; orgparse already exposes it.
- *JSON surface* → additive `updated`/`created` on `idea_row`, omitted when absent.
- *Scope beyond ideas* → idea-only; `set_state`/`set_property` guard on `task.is_idea`.
- *Write churn* → one write per mutation by injecting into the existing write; pinned by a test.
- *Resolution display* → out of scope; the column belongs to SPEC-0075's follow-up.
