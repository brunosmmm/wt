---
id: SPEC-0125
title: "wt sheet plan/record JSON CLI"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
source_idea: IDEA-207
parent: SPEC-0123
milestone: "M7: sheet sync"
tags: [ideas, sync, sheets, cli]
depends_on: [SPEC-0124]
---

## Context

Promoted from idea `IDEA-207` (SPEC-0125).

  :PROPERTIES:
  :ID: IDEA-207
  :CREATED: [2026-08-04 Tue 17:14]
  :UPDATED: [2026-08-04 Tue 17:14]
  :PROJECT: Meta-Tools
  :EPIC: SPEC-0123
  :END:
** Summary
Child of epic `SPEC-0123`.

SPEC-0125 (project: Meta-Tools) — `wt sheet plan`/`wt sheet record` JSON CLI (depends_on SPEC-0124)
** Open questions

** Log

## Goals / Non-goals

**Goals**
- `wt sheet plan --project <P>`: a pure, local, JSON-only computation of what a sync run
  would need to *push* (ideas whose wt-owned content changed or were never pushed) — using
  only the local idea corpus + SPEC-0124's manifest, no network access, ever.
- The same command, given a `--sheet-rows` JSON snapshot of the sheet's current rows
  (supplied by whatever already fetched it — the driving agent, via its own MCP tools), also
  computes what to *pull*: which of those rows are unknown locally (candidates to adopt as
  new ideas).
- `wt sheet record --project <P>`: takes a JSON payload describing a sync run's outcome
  (which ideas got pushed as which row ids, which rows got adopted as which new ideas) and
  persists the bookkeeping — `sheet_row`/`sheet_hash` under `Ext <P>` — via the existing
  `idea_ext` mutators (SPEC-0119/0122). Also captures brand-new ideas for adopted rows.
- Enforce the sync scope invariant from SPEC-0123: only `:PROJECT: P` ideas with
  `Ext P.sheet_sync == "yes"` are ever included in a push plan.

**Non-goals**
- Any Sheets API call, or any new runtime dependency — `plan`/`record` operate purely on the
  local idea corpus, the manifest, and (for `plan --sheet-rows`) a JSON blob the caller
  already obtained some other way. This is the concrete fulfillment of SPEC-0123's
  transport-agnostic invariant.
- Automatic conflict *resolution* — a divergent wt-owned column is reported as a conflict in
  the plan output; resolving it (re-push with `--force`, or accept the sheet's version) is a
  human/skill-level decision, not something `plan`/`record` do silently.
- Reconciling `sheet_row` ids against Example's separate outbound `docs/specs` counter (the
  residual risk flagged on IDEA-200/SPEC-0123) — `sheet_row` values are supplied externally
  (minted by whatever process adds a sheet row) and simply stored; this child does not mint
  ids itself.
- The `/wt-sheet-sync` skill that actually drives a real sync end-to-end — SPEC-0126.

## Decision

Add `src/wt/sheet_sync.py` with three pure functions — `plan_push`, `plan_pull`, `record` —
and a new `wt sheet` Click group (`plan`, `record`) in `cli.py` that JSON-serializes their
output. `plan_push` walks `filter_tasks(load_tasks(cfg), project=P, is_idea=True)`, keeps only
ideas with `Ext P.sheet_sync == "yes"` (`idea_ext.read_idea_extension`), renders each
manifest-declared wt-owned column's current value from the idea, and hashes those values
(excluding the id column itself) to compare against the idea's stored `Ext P.sheet_hash`.
`plan_pull` (only when `--sheet-rows` is given) flags sheet rows whose id-column value isn't
any known idea's `Ext P.sheet_row` as adoption candidates. `record` takes back a `{pushed:
[...], adopted: [...]}` payload and writes `Ext P.sheet_row`/`sheet_hash` (recomputed at
record time) onto the relevant ideas via `idea_ext.set_idea_extension`, capturing a new idea
per adopted row first.

## Design

**`src/wt/sheet_sync.py`** (new module):

```python
def _row_value(col: SheetColumn, task, ext: dict) -> str:
    if col.source == "id":
        return ext.get("sheet_row", "")
    if col.source == "title":
        return task.heading
    if col.source == "status":
        return task.state or ""
    return ext.get(col.source, "")   # freeform passthrough for other wt-sourced fields

def render_row(manifest, task, ext) -> dict[str, str]:
    """header -> value, for every wt-owned column."""

def content_hash(manifest, task, ext) -> str:
    """sha256 hex over render_row(), excluding the id_column (bookkeeping, not content)."""

def plan_push(cfg, project) -> list[dict]:
    """One entry per idea needing push:
    {"idea": "IDEA-127", "row_id": "EXAMPLE-0009" | None, "action": "new" | "update",
     "row": {header: value, ...}}
    Skips ideas whose computed hash matches the stored Ext sheet_hash (nothing changed)."""

def plan_pull(cfg, project, sheet_rows: list[dict]) -> list[dict]:
    """sheet_rows: [{header: value, ...}, ...] as already fetched by the caller. Returns rows
    whose id-column value matches no known idea's Ext sheet_row:
    [{"row": {...}, "reason": "unknown-id"}]"""

def make_plan(cfg, project, sheet_rows=None) -> dict:
    """{"project": P, "manifest": name, "push": plan_push(...),
        "pull": plan_pull(...) if sheet_rows is not None else []}"""

def record(cfg, project, payload: dict) -> dict:
    """payload: {"pushed": [{"idea": "IDEA-127", "row_id": "EXAMPLE-0009"}, ...],
                 "adopted": [{"row_id": "EXAMPLE-0010", "title": "...", ...}, ...]}
    For each pushed entry: idea_ext.set_idea_extension(cfg, idea, "sheet_row", row_id,
    project=project) then "sheet_hash" recomputed from the idea's current content.
    For each adopted entry: capture a new idea (`org_write` capture path used by `wt idea`),
    stamp :PROJECT: project, then set sheet_row/sheet_hash/sheet_sync=yes on it.
    Returns {"pushed": [idea_ids...], "adopted": [new_idea_ids...]}."""
```

**`src/wt/cli.py`** — new group:

```
wt sheet plan --project <P> [--sheet-rows PATH|-]   # JSON to stdout, always
wt sheet record --project <P> --payload PATH|-       # JSON payload in, JSON summary out
```

Both commands are JSON-only (no `--json` flag needed/offered) — this surface is for the
driving agent/skill, not interactive human use, consistent with SPEC-0123's Architecture
(`wt` never touches the network; everything here is local JSON in/out). `--sheet-rows`/
`--payload` accept a file path or `-` for stdin.

## Alternatives considered

- **Recompute/verify a pushed idea's hash against the plan's precomputed value at `record`
  time** (to catch drift between `plan` and the actual push) — deferred; `record` simply
  recomputes fresh from current idea state, which is simpler and correct for the common
  case (no other write happens between `plan` and `record` in one sync run). Documented here
  rather than silently assumed.
- **`plan` also emits sheet-owned column values for existing rows** — rejected; wt does not
  track sheet-owned data at all (SPEC-0123 invariant), so there is nothing meaningful to diff
  there; a human-owned column is always taken as-is by whoever reads the sheet.
- **A single `wt sheet sync` command doing plan+record in one call** — rejected; would require
  wt to make the Sheets call itself, which SPEC-0123 rules out. Two JSON-only halves with the
  actual API calls sandwiched in between (by the skill) is the only shape consistent with
  that constraint.

## Acceptance criteria

- [x] `wt sheet plan --project Example` lists exactly the ideas with `:PROJECT: Example` and
      `Ext Example.sheet_sync = yes` needing push (new: no `sheet_row` yet; update: hash
      differs from stored `sheet_hash`), and omits unchanged ones.
- [x] `wt sheet plan --project Example --sheet-rows <file>` additionally lists sheet rows whose
      id isn't any known idea's `sheet_row`, under `pull`.
- [x] `wt sheet record --project Example --payload <file>` with a `pushed` entry sets that
      idea's `Ext Example.sheet_row`/`sheet_hash` such that a following `wt sheet plan` no
      longer lists it (until it changes again).
- [x] `record` with an `adopted` entry creates a new idea (`:PROJECT: Example`) with
      `Ext Example.sheet_row`/`sheet_hash`/`sheet_sync = yes` already set.
- [x] An idea with `:PROJECT: Example` but no `Ext Example.sheet_sync = yes` (absent or `no`)
      never appears in any plan output.
- [x] No network call anywhere in `sheet_sync.py` or the new CLI commands — by inspection:
      the module imports only `idea_ext`/`org_write`/`org`/`sheet_schemes` (all local, no
      HTTP/socket library), and `pyproject.toml` gained no new dependency.

## Test plan

- **Automated tests:** `tests/test_sheet_sync.py` (9 tests) — fixture ideas with varying `Ext`
  state (no `sheet_sync`, `sheet_sync=yes` + no `sheet_row`, matching hash, stale hash after a
  retitle) exercising `plan_push`/`plan_pull`/`record`/`make_plan` directly; `CliRunner` tests
  for `wt sheet plan`/`wt sheet record` round-tripping JSON via a tmp payload file, plus an
  unknown-project error case.
- **Manual verification:** the `test_cli_sheet_plan_and_record` test itself is the manual
  scenario automated — push an idea, record it, confirm a second `plan` shows it clean; ran it
  directly (`uv run pytest tests/test_sheet_sync.py -q` → 8 passed at authxxing time, 9 after
  adding the unknown-project case).
- **Regression guard:** `uv run pytest` green (1086 passed); existing idea/Ext/export-scheme
  tests unaffected.

## Rollout / migration

Land after SPEC-0124. Purely additive: new module + new CLI group, no changes to existing
idea/Ext/export code paths beyond calling their existing public functions.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — scope is fully determined by SPEC-0123's Architecture)

## What shipped / deviations

Implemented as designed: `src/wt/sheet_sync.py` (`render_row`/`content_hash`/`plan_push`/
`plan_pull`/`make_plan`/`record`), a new `wt sheet` Click group in `cli.py` (`plan`, `record`,
both JSON-only via a shared `_read_json_arg` file-or-stdin helper). One naming deviation from
the Design sketch: internal helpers `_record_pushed`/`_record_adopted` factor out the two
payload-entry kinds `record` handles, rather than one large inline loop — same public
contract, easier to test in isolation. `content_hash` excludes the id column from the hashed
payload exactly as designed, so re-recording an unchanged idea correctly no-ops on the next
`plan`.
