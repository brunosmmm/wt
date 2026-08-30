---
id: SPEC-0127
title: "Sheet-sync column value maps (neutral external vocabulary)"
status: done
owner: user
created: 2026-08-05
updated: 2026-08-05
source_idea: IDEA-226
milestone: "M7: sheet sync"
tags: [ideas, sync, sheets, bugfix]
depends_on: [SPEC-0124, SPEC-0125]
---

## Context

Promoted from idea `IDEA-226` (Sheet-sync Status column leaks wt's internal idea-state vocabulary (SPECCED/INCUBATE/...) into the external sheet instead of a neutral dev-stage label).

  :PROPERTIES:
  :ID: IDEA-226
  :CREATED: [2026-08-05 Wed 15:20]
  :UPDATED: [2026-08-05 Wed 17:21]
  :PROJECT: Meta-Tools
  :KIND: bug
  :EXPLORED: 1
  :EXPLORED_AT: [2026-08-05 Wed 17:21]
  :END:
** Summary
Found while running the first real sheet-sync test (SPEC-0123 epic) against Example's
Pre-triage Backlog: pushed rows showed `Status`SPECCED` / `Status`INCUBATE` -- wt's own
internal idea-state vocabulary (org TODO keywords) -- verbatim in the external, customer-
facing sheet. The human correctly flagged this as unacceptable: the sheet needs neutral,
common-sense dev-stage language, not wt jargon.

Root cause: `sheet_sync.render_row()`'s `_row_value()` (source == "status") returns
`task.state` raw, and that same raw value feeds `content_hash()`. This means the fix
**cannot** be a display-only patch (e.g. done in the /wt-sheet-sync skill's prose, or by
hand-editing the sheet after the fact) -- if the hashed value and the displayed value
diverge, future `wt sheet plan` runs will either loop on false "changed" detections or
silently miss real changes. The mapping has to live in the rendering code itself, applied
before both display and hashing.

Design: extend `SheetColumn` (`src/wt/sheet_schemes.py`, SPEC-0124) with an optional
per-column value map (e.g. a `status_map` table in the TOML manifest, keyed by the raw wt
value); `sheet_sync.render_row()` (SPEC-0125) applies it when present, falling back to the
raw value when a wt state isn't in the map (fail-loud candidate: unmapped values probably
should not push at all, or push a placeholder -- open question below).

Agreed neutral vocabulary (human-confirmed) for Example's manifest:
- IDEA, INCUBATE -> New
- SPECCED -> Planned
- PROMOTED, EXPORTED -> In Progress
- DROPPED -> Dropped
- RESEARCHED -> Researched

Stopgap already applied by hand (2026-08-05): the 3 live rows already pushed
(EXAMPLE-0026/0027/0028) had their Status cells manually corrected to Planned/New/New in the
actual sheet. wt's own stored `Ext Example.sheet_hash` for those 3 ideas still reflects the
**raw** pre-fix render (SPECCED/INCUBATE), so once the real manifest-mapping fix ships, the
first `wt sheet plan` afterward will very likely (correctly) flag all 3 as changed --
expected, not a bug, since the hash was computed before the fix existed.
** Open questions
*** RESOLVED Unmapped wt state (a status_map present but missing an entry for some state): fall back to the raw wt value (current behavior), a configured default (e.g. 'Unknown'), or hard-fail the push until the manifest is updated?
Resolved: fall back to the raw wt value AND print a stderr warning naming the column header and the unmapped value. Rationale: hard-failing the whole push over one unmapped state blocks unrelated pushes in the same run (too harsh); a generic 'Unknown' default hides real information a viewer might want (which raw state it actually is) with no signal that the manifest is incomplete. Raw-value-plus-warning matches the existing permissive-but-visible pattern extension_schema.py already uses for unknown idea_extensions project names.
*** RESOLVED Scope: is a value map needed only for the Status column, or should any wt-owned column support this (e.g. a future column reusing wt's :PRIORITY: A/B/C cookie translated to High/Medium/Low)? Generalize now or special-case Status first?
Resolved: generalize now, not Status-only. A generic value_map: dict[str,str] on SheetColumn (SPEC-0124), applied uniformly in render_row() (SPEC-0125) regardless of the column's source, costs almost nothing extra (one optional TOML subtable + one small helper) versus a Status-specific mechanism, and avoids a second migration the moment a :PRIORITY:-backed column shows up.
*** RESOLVED This changes SPEC-0124 (SheetColumn shape) and SPEC-0125 (render_row/content_hash) after both shipped 'done' -- new child spec under SPEC-0123, or a small standalone spec since the epic itself is closed?
Resolved: a small standalone feature spec, not a new child under SPEC-0123. SPEC-0123 is kind: epic and status: done, and the epic model (SPEC-0003/SCHEMA.md) treats 'done while all children done/superseded' as a completed unit -- adding a new child would mean reopening it. A standalone spec with depends_on: [SPEC-0124, SPEC-0125] (and tags noting the SPEC-0123 lineage) is cleaner and matches how SPEC-0058 followed up on SPEC-0016 without being folded back into an epic.
** Log
*** [2026-08-05 Wed 17:21]
Explore pass: confirmed via a tomllib smoke test that [[columns]] followed by [columns.value_map] attaches correctly to the last array element (standard TOML dotted-table-after-array-of-tables behavior) -- the manifest syntax sketched in the Summary parses as intended. All 3 open questions resolved (see question rationale bodies): warn-and-fallback for unmapped values, generalize value_map to any column (not Status-only), standalone spec (not a new SPEC-0123 child, since that epic is done).

## Goals / Non-goals

**Goals**
- Let a sheet manifest declare an optional value-translation table on any column, so wt's
  internal vocabulary (idea states today; potentially `:PRIORITY:` cookies later) never has
  to leak verbatim into an external, customer-facing sheet.
- Apply the mapping in exactly one place, before both display and hashing, so
  `content_hash()` and the actually-written cell can never diverge.
- Fail soft: an unmapped raw value still pushes (as itself), with a visible warning, rather
  than blocking an entire sync run over one incomplete manifest entry.

**Non-goals**
- A generic i18n/locale layer — this is a flat string→string table per column, nothing more.
- Retroactively fixing the 3 rows already hand-patched in the live sheet as a stopgap — this
  spec's Rollout explicitly expects (and accepts) that the next real `wt sheet plan` after
  landing will flag them as `action: "update"` once their hash is recomputed with the mapping
  applied; that's correct behavior, not something to special-case around.
- Reopening or modifying `SPEC-0123` (the closed epic) — this stands alone, `depends_on`
  `SPEC-0124`/`SPEC-0125` for the shapes it extends.

## Decision

Add an optional `value_map: dict[str, str]` field to `SheetColumn` (`src/wt/sheet_schemes.py`,
SPEC-0124), populated from an optional `[columns.value_map]` TOML subtable per column entry.
`sheet_sync.render_row()` (SPEC-0125) applies it uniformly to every column's raw value (not
just `Status`) before both display and hashing: a mapped value substitutes; an unmapped one
falls back to the raw value with a `stderr` warning naming the column and the value.

## Design

**`src/wt/sheet_schemes.py`** (SPEC-0124 extension):

```python
@dataclass(frozen=True)
class SheetColumn:
    header: str
    source: str
    owner: str
    value_map: dict = field(default_factory=dict)   # NEW, optional
```

`_parse_manifest` reads an optional `value_map` table off each `columns[]` entry (TOML shape
confirmed by a `tomllib` smoke test during explore: `[[columns]] ... [columns.value_map]`
attaches correctly to the last array element). Validates: if present, must be a table whose
keys/values are all non-empty strings — same fail-closed posture as the rest of manifest
parsing.

**`src/wt/sheet_sync.py`** (SPEC-0125 extension):

```python
def _apply_value_map(col: SheetColumn, raw: str) -> str:
    if not col.value_map:
        return raw
    if raw in col.value_map:
        return col.value_map[raw]
    if raw:
        print(f"! sheet column {col.header!r}: no value_map entry for {raw!r}; "
              f"using raw value", file=sys.stderr)
    return raw
```

`_row_value()` computes the raw value exactly as today (id/title/status/passthrough), then
`render_row()` pipes each through `_apply_value_map(col, raw)` before building the row dict
that both the display write and `content_hash()` consume — guaranteeing they can never
diverge (the root-cause invariant from IDEA-226's Summary).

**Example manifest update** (`~/.config/wt/schemes/example-pretriage-sheet.toml`, not part of
this repo, applied alongside landing this spec):

```toml
[[columns]]
header = "Status"
source = "status"
owner = "wt"
[columns.value_map]
IDEA = "New"
INCUBATE = "New"
SPECCED = "Planned"
PROMOTED = "In Progress"
EXPORTED = "In Progress"
DROPPED = "Dropped"
RESEARCHED = "Researched"
```

## Alternatives considered

- **Hard-fail the push on an unmapped value** — rejected; blocks unrelated ideas in the same
  sync run over one incomplete manifest entry (resolved on IDEA-226 Q1).
- **A configured default label (e.g. "Unknown") instead of raw fallback** — rejected; hides
  which specific wt state is unmapped, giving the manifest authxx less to go on when fixing it.
- **Special-case `Status` only** (e.g. a `status_map` field instead of a generic column
  `value_map`) — rejected; a generic mechanism is barely more code and avoids a second
  migration the moment another wt-owned column (e.g. one backed by `:PRIORITY:`) wants the
  same treatment (resolved on IDEA-226 Q2).
- **Translate in the `/wt-sheet-sync` skill's prose instead of in code** — rejected outright;
  this is the root cause being fixed, not a valid alternative (a skill-level translation
  can't keep the hash and the displayed value consistent).

## Acceptance criteria

- [x] A manifest column with a `value_map` renders the mapped value in both `render_row()`'s
      output and in `content_hash()`'s input — never the raw wt value
      (`test_content_hash_uses_mapped_value_not_raw` proves IDEA/INCUBATE hash identically
      since both map to "New").
- [x] A manifest column with no `value_map` behaves exactly as before (no regression) —
      `test_render_row_no_value_map_is_unaffected`.
- [x] A raw value with no entry in a present `value_map` still renders (falls back to itself)
      and prints exactly one `stderr` warning naming the column header and the value —
      `test_render_row_unmapped_value_falls_back_with_warning`.
- [x] The mechanism works for any column, not just `Status` — `SheetColumn.value_map` is a
      generic field applied uniformly by `_apply_value_map`, not special-cased to any source.
- [x] Example's manifest is updated with the agreed neutral vocabulary (IDEA/INCUBATE→New,
      SPECCED→Planned, PROMOTED/EXPORTED→In Progress, DROPPED→Dropped,
      RESEARCHED→Researched), and a live `wt sheet plan --project Example` rendered neutral
      labels for all 8 already-synced ideas, correctly flagged as `action: "update"` since
      their stored hash predated this fix — pushed + recorded; follow-up `plan` is clean.

## Test plan

- **Automated tests:** `tests/test_sheet_schemes.py` gained `test_load_manifest_with_value_map`
  + 2 invalid-shape cases (3 new, 15 total in the file); `tests/test_sheet_sync.py` gained 4
  new cases (`render_row_applies_value_map`, `content_hash_uses_mapped_value_not_raw`,
  `render_row_unmapped_value_falls_back_with_warning`, `render_row_no_value_map_is_unaffected`
  — 12 total in the file, 27 combined).
- **Manual verification:** updated the real `~/.config/wt/schemes/example-pretriage-sheet.toml`
  with the neutral-vocabulary table; ran `wt sheet plan --project Example` — all 8 rows showed
  `action: "update"` with neutral `Status` values (`New`/`Planned`/`In Progress`) matching
  what was already hand-patched in the live sheet; pushed + recorded via `wt sheet record`;
  follow-up `wt sheet plan --project Example` returned an empty `push`/`pull`.
- **Regression guard:** `uv run pytest` green (1095 passed); existing no-`value_map` manifest
  cases unchanged in behavior.

## Rollout / migration

Land the code change, then update the live Example manifest. The very next `wt sheet plan`
after that will correctly flag the 8 already-synced ideas as needing an update (their stored
`sheet_hash` predates the mapping) — push + record them once to bring the sheet's actual
`Status` cells (currently hand-patched stopgaps) under the mechanism's control, replacing the
manual patch with a real, hash-consistent one.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — resolved on IDEA-226 before accept)

## What shipped / deviations

Implemented exactly as designed: `SheetColumn.value_map` (SPEC-0124 extension, validated
fail-closed in `_parse_manifest`), `_apply_value_map`/`_raw_row_value`/`_row_value` in
`sheet_sync.py` (SPEC-0125 extension) — `render_row` and `content_hash` both flow through the
same mapped values with zero extra code in `content_hash` itself, since it already delegates
to `render_row`. No deviations from the Design. Example's live manifest now carries the
human-confirmed neutral vocabulary, and the 8 live sheet rows (previously hand-patched
stopgaps) are now backed by a real, hash-consistent mechanism instead of a manual edit.
