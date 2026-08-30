---
id: SPEC-0124
title: "Sheet-sync manifest format + outbox_targets.sheet config"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
source_idea: IDEA-206
parent: SPEC-0123
milestone: "M7: sheet sync"
tags: [ideas, sync, sheets, config]
---

## Context

Promoted from idea `IDEA-206` (SPEC-0124).

  :PROPERTIES:
  :ID: IDEA-206
  :CREATED: [2026-08-04 Tue 17:13]
  :UPDATED: [2026-08-04 Tue 17:14]
  :PROJECT: Meta-Tools
  :EPIC: SPEC-0123
  :END:
** Summary
Child of epic `SPEC-0123`.

SPEC-0124 (project: Meta-Tools) — Sheet-sync manifest format + `outbox_targets[project].sheet` config
** Open questions

** Log

## Goals / Non-goals

**Goals**
- A declarative TOML manifest describing one Google Sheet's column mapping: which columns
  wt owns (pushes) vs which the sheet/human owns (wt only reads them back) — the data model
  child SPEC-0125's plan/record CLI will consume.
- A loader for these manifests from `<config_dir>/schemes/` (same directory
  `export_schemes/template_scheme.py` already loads user export manifests from, per
  SPEC-0058), disambiguated by a `kind = "sheet"` field so it never collides with (or gets
  mistakenly registered as) an `ExportScheme`.
- A `outbox_targets[project].sheet` config key (`spreadsheet_id`, `tab`, `manifest`) resolving
  a project to its manifest, mirroring how `outbox_targets[project].repo_path`/`spec_dir`
  already resolve a project to its outbound export destination.
- Fail-closed validation of both the manifest shape and the config pointer, with clear error
  messages (same posture as `extension_schema.py`'s `normalize_extension_schema`).

**Non-goals**
- Any Sheets API call, or any new runtime dependency in `pyproject.toml` — this child is pure
  data model + config, no network code at all (SPEC-0123 Architecture invariant).
- The actual push/pull diff logic, Ext bookkeeping, or CLI surface (`wt sheet plan`/`record`)
  — SPEC-0125.
- Shipping a built-in/in-tree manifest (unlike `template_scheme.py`'s `manifests/` dir of
  built-in export schemes) — every sheet manifest is inherently org/sheet-specific and lives
  only in `<config_dir>/schemes/` (SPEC-0123 Decision).
- A `Schema` tab inside the Google Sheet itself — optional future documentation, not part of
  this child's contract.

## Decision

Add `src/wt/sheet_schemes.py`: a `SheetManifest` data model (`name`, `description`,
`id_column`, `columns: [SheetColumn(header, source, owner)]`) loaded from TOML files under
`<config_dir>/schemes/` that declare `kind = "sheet"`; `template_scheme.py`'s existing loader
is changed to skip any manifest with `kind = "sheet"` so the two manifest families coexist in
one directory without colliding. `outbox_targets[project].sheet` is a new (freeform, already
supported by `config.py`'s generic dict merge) config key resolved by
`resolve_sheet_manifest(cfg, project)`, which raises a clear `ValueError` when the project has
no `sheet` target or the named manifest is missing/invalid.

## Design

**`src/wt/sheet_schemes.py`** (new module):

```python
@dataclass
class SheetColumn:
    header: str            # exact sheet column header, e.g. "Feature"
    source: str            # logical field name: "id" | "title" | "status" | free-form
    owner: str              # "wt" | "sheet" — SPEC-0123's column-ownership split

@dataclass
class SheetManifest:
    name: str
    description: str
    id_column: str          # which column's header is the join-key id (must be owner="wt")
    columns: tuple[SheetColumn, ...]
    origin: str = "user-config"   # always "user-config" (no built-ins, see Non-goals)

    def column(self, header) -> SheetColumn | None: ...
    def wt_owned(self) -> tuple[SheetColumn, ...]: ...
    def sheet_owned(self) -> tuple[SheetColumn, ...]: ...
```

- `load_manifest(path) -> SheetManifest`: parses TOML, validates: `id_column` must name a
  column present in `columns` with `owner == "wt"`; every column's `owner` must be
  `"wt"`/`"sheet"`; headers unique. Raises `ValueError` (with the offending manifest path) on
  any violation — fail-closed, same posture as `extension_schema.normalize_extension_schema`.
- `available_sheet_manifests(cfg) -> dict[str, SheetManifest]`: scans
  `<config_dir>/schemes/*.toml`, parses each, keeps only `kind == "sheet"` (silently skips
  export-scheme manifests — they lack `kind` entirely or declare something else), keyed by
  `name`.
- `get_sheet_manifest(cfg, name) -> SheetManifest`: looks up in `available_sheet_manifests`;
  raises `ValueError` listing available names when absent (mirrors
  `export_schemes.get`'s error shape).
- `sheet_target_for(cfg, project) -> dict | None`: `(cfg.get("outbox_targets") or
  {}).get(project, {}).get("sheet")` — `None` when the project has no sheet target
  configured (freeform dict otherwise, validated by the next function).
- `resolve_sheet_manifest(cfg, project) -> tuple[dict, SheetManifest]`: calls
  `sheet_target_for`; raises `ValueError` if `None`, or if the target dict is missing
  `spreadsheet_id`/`tab`/`manifest`, or if `get_sheet_manifest` fails — always a single clear
  error, never a partial/ambiguous result.

**`src/wt/export_schemes/template_scheme.py`** (one-line change): `_load_manifest`'s callers
(`load_manifests_from`) skip any parsed manifest dict with `manifest.get("kind") == "sheet"`
before constructing a `TemplateScheme` — export manifests are unaffected (they have no `kind`
key today, so this is a strictly additive filter).

**Config**: no `config.py` change needed — `outbox_targets` is already a freeform
per-project dict merged shallowly (`config.py:83-87`), so a new `sheet:` sub-key under any
project entry works with zero code change; only documented via a comment + example in
`~/.config/wt/config.yaml`-shaped test fixtures.

Example manifest (`~/.config/wt/schemes/example-pretriage-sheet.toml`, illustrative — the real
file ships with SPEC-0126):

```toml
kind = "sheet"
name = "example-pretriage-sheet"
description = "Example Pre-triage Backlog tab column mapping"
id_column = "ID"

[[columns]]
header = "ID"
source = "id"
owner = "wt"

[[columns]]
header = "Feature"
source = "title"
owner = "wt"

[[columns]]
header = "Status"
source = "status"
owner = "wt"

[[columns]]
header = "Costumer"
source = "costumer"
owner = "sheet"
```

## Alternatives considered

- **A separate `<config_dir>/sheet-schemes/` directory** — rejected; SPEC-0123's Decision
  already commits to reusing `<config_dir>/schemes/` (one place for "manifests I authxxed for
  my own integrations"), and a `kind` discriminator is a one-line filter, not worth a second
  directory convention.
- **JSON Schema for the manifest** — rejected as over-engineering for four fields per column;
  matches SPEC-0120's own rejection of full JSON Schema for `idea_extensions`.
- **Folding this into `template_scheme.py`/`TemplateScheme` directly** (one class handling
  both section-based and column-based manifests) — rejected; the two shapes (prose sections
  vs. spreadsheet columns) don't share enough structure to justify one class, and it would
  make `ExportScheme`'s `render(ctx: RenderContext, ...)` contract (which assumes a
  `CanonicalSpec`, a *spec* concept) leak into what is actually an *idea*-level integration.

## Acceptance criteria

- [x] A `kind = "sheet"` TOML manifest under `<config_dir>/schemes/` loads into a
      `SheetManifest` with correctly split `wt_owned()`/`sheet_owned()` columns.
- [x] A manifest missing `id_column`, with `id_column` not present in `columns`, with
      `id_column`'s column `owner != "wt"`, with an invalid `owner` value, or with duplicate
      headers fails to load with a clear `ValueError`.
- [x] `outbox_targets[project].sheet` with `spreadsheet_id`/`tab`/`manifest` resolves via
      `resolve_sheet_manifest` to the matching `SheetManifest`.
- [x] A project with no `sheet` target returns `None` from `sheet_target_for` (freeform,
      unconfigured — no error) and raises a clear error only when `resolve_sheet_manifest` is
      actually called for it.
- [x] `template_scheme.py`'s existing manifest loading is unaffected: a `kind = "sheet"`
      manifest dropped in `<config_dir>/schemes/` never appears in `wt spec schemes`'/
      `export_schemes.available()`'s output.
- [x] No new dependency added to `pyproject.toml`.

## Test plan

- **Automated tests:** `tests/test_sheet_schemes.py` (12 tests) — fixture manifests (valid;
  6 invalid shapes) exercised via `load_manifest`/`available_sheet_manifests`/
  `get_sheet_manifest`; `sheet_target_for`/`resolve_sheet_manifest` against fixture `cfg`
  dicts (present/absent/malformed `sheet` key); a dedicated test asserts a `kind = "sheet"`
  manifest dropped in `<config_dir>/schemes/` never shows up in
  `export_schemes.available()`.
- **Manual verification:** ran `SS.resolve_sheet_manifest` against a tmp-dir manifest
  matching the Example example in Design, via the test suite's own fixtures (equivalent to the
  planned one-liner — same code path, exercised by `test_sheet_target_for_and_resolve`).
- **Regression guard:** `uv run pytest` green (1080 passed), including unchanged
  `tests/test_export_schemes.py`.

## Rollout / migration

Pure addition: new module, one filter line in `template_scheme.py`, no config schema change.
Land before SPEC-0125 (which imports `sheet_schemes` for its plan/record diff logic).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — scope is fully determined by SPEC-0123's Architecture)

## What shipped / deviations

Implemented exactly as designed: `src/wt/sheet_schemes.py` (`SheetColumn`/`SheetManifest`
dataclasses, `load_manifest`/`available_sheet_manifests`/`get_sheet_manifest`/
`sheet_target_for`/`resolve_sheet_manifest`), plus a one-line-of-intent filter in
`export_schemes/template_scheme.py`'s `load_manifests_from` skipping `kind = "sheet"`
manifests. One deviation from the Design sketch: the schemes directory is resolved per-call
(`_user_schemes_dir()`) rather than as a module-level constant like
`template_scheme.py`'s `_USER_SCHEMES_DIR` — this avoids needing `importlib.reload` gymnastics
in tests, since `sheet_schemes.py` (unlike `template_scheme.py`) doesn't populate a
module-level registry at import time.
