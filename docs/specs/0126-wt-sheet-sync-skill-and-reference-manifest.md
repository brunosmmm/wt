---
id: SPEC-0126
title: "wt-sheet-sync skill and reference sheet-sync manifest"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
source_idea: IDEA-208
parent: SPEC-0123
milestone: "M7: sheet sync"
tags: [ideas, sync, sheets, skill]
depends_on: [SPEC-0124, SPEC-0125]
---

## Context

Promoted from idea `IDEA-208` (SPEC-0126).

  :PROPERTIES:
  :ID: IDEA-208
  :CREATED: [2026-08-04 Tue 17:14]
  :UPDATED: [2026-08-04 Tue 17:14]
  :PROJECT: Meta-Tools
  :EPIC: SPEC-0123
  :END:
** Summary
Child of epic `SPEC-0123`.

SPEC-0126 (project: Meta-Tools) — `/wt-sheet-sync` skill + reference sheet-sync manifest/config (depends_on SPEC-0124, SPEC-0125)
** Open questions

** Log

## Goals / Non-goals

**Goals**
- A `/wt-sheet-sync` skill (repo-versioned, `skills/wt-sheet-sync/SKILL.md`, installed the
  same way every other `wt-*` skill is — SPEC-0017) that orchestrates a full sync run: call
  `wt sheet plan`, drive the actual Google Sheets reads/writes via the operator's own Sheets
  MCP tools, then call `wt sheet record` with the outcome.
  the operator's own Sheets MCP tools, then call `wt sheet record` with the outcome.
- Ship the first real `SheetManifest` instance (`example-pretriage-sheet.toml`) and wire Example's
  `outbox_targets.Example.sheet` config + optional `idea_extensions.Example` schema entries for
  `sheet_sync`/`sheet_row`/`sheet_hash` — the reference example other projects copy, closing
  the loop the whole epic was built for.

**Non-goals**
- Actually flipping any real idea's `Ext Example.sheet_sync` to `yes`, or running a sync against
  the live Pre-triage Backlog tab. SPEC-0123's Rollout explicitly gates that on (a) fixing the
  sheet's existing duplicate `EXAMPLE-0002` id by hand and (b) a verified dry run against a
  disposable copy/tab — neither is this child's job.
- Committing the manifest file into `wt`'s own repo — per SPEC-0123's Decision it lives in
  `~/.config/wt/schemes/` (this machine's config, mirroring `static-boilerplate-example.toml`'s
  precedent), not `docs/` or `src/`.
- Any new library code — SPEC-0124/0125 already provide everything this child orchestrates.

## Decision

Ship `skills/wt-sheet-sync/SKILL.md` describing the plan → MCP → record loop (see Design for
the exact procedure), and materialize the reference config on this machine: a
`example-pretriage-sheet.toml` manifest matching the Pre-triage Backlog's real (if bare) columns,
an `outbox_targets.Example.sheet` block pointing at the real spreadsheet/tab, and an
`idea_extensions.Example` schema entry declaring `sheet_sync`/`sheet_row`/`sheet_hash` as
optional properties (so CLI/desk enum completion works for `sheet_sync`, per SPEC-0122).

## Design

**`skills/wt-sheet-sync/SKILL.md`** — procedure the skill teaches an agent:

1. Confirm the target project has a sheet target: `wt sheet plan --project <P>` (errors with a
   clear message, per SPEC-0124/0125, if `outbox_targets[P].sheet` isn't configured).
2. Read the current sheet contents via the operator's own Google Sheets MCP tools (e.g.
   `sheets_batch_get`/`google_sheets_read_range`) for the configured `tab`; shape each row into
   `{header: value}` matching the manifest's declared headers; write to a tmp JSON file.
3. `wt sheet plan --project <P> --sheet-rows <tmp-file>` — now with both `push` and `pull`
   populated.
4. For each `push` entry: upsert that row into the sheet (new row if `row_id` is `None`,
   update in place by id if not) via the Sheets MCP tools, using the manifest's column headers
   — never touch a `sheet`-owned column's existing value.
5. For each `pull` entry (an unknown row): decide with the operator whether to adopt it (skill
   default: adopt, since it's exactly what "pre-triage backlog" rows are for).
6. Build the outcome payload (`{"pushed": [...], "adopted": [...]}`) from what actually
   happened in steps 4–5, write it to a tmp file, `wt sheet record --project <P> --payload
   <file>`.
7. Report a short summary (counts pushed/adopted/skipped) back to the operator — never claim
   success without having actually called `record`.

**Reference manifest** (`~/.config/wt/schemes/example-pretriage-sheet.toml`, this machine):

```toml
kind = "sheet"
name = "example-pretriage-sheet"
description = "Example Pre-triage Backlog tab column mapping (SPEC-0123/0126)"
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

**Config wiring** (`~/.config/wt/config.yaml`, additive):

```yaml
outbox_targets:
  Example:
    sheet:
      spreadsheet_id: "1JFGArwv8QoWwQRushxjkV7tbd8nxp465sWg1Q5tPXLs"
      tab: "Pre-triage Backlog"
      manifest: example-pretriage-sheet

idea_extensions:
  Example:
    required: []
    properties:
      sheet_sync: { type: enum, values: ["yes", "no"] }
      sheet_row: { type: string }
      sheet_hash: { type: string }
```

## Alternatives considered

- **Fold this procedure into the existing `/wt-export` skill** — rejected for the same reason
  SPEC-0123 kept `wt sheet` separate from `wt spec export`: different lifecycle stage (idea,
  not spec) and a fundamentally different transport (live API round-trip via MCP tools vs.
  file-drop). A shared skill would have to branch its entire procedure on which mode it's in.
- **Auto-adopt every unknown row without asking** — rejected as the skill's hard-coded
  default; documented instead as the skill's *suggested* default so an operator can override
  per run (a pre-triage backlog may contain rows nobody wants captured as a wt idea yet).

## Acceptance criteria

- [x] `wt skills install` (or an equivalent listing) picks up `wt-sheet-sync` alongside every
      other `wt-*` skill with zero registry change (SPEC-0017's directory-scan mechanism).
- [x] `~/.config/wt/schemes/example-pretriage-sheet.toml` loads via
      `sheet_schemes.get_sheet_manifest(cfg, "example-pretriage-sheet")` without error.
- [x] `sheet_schemes.resolve_sheet_manifest(load_config(), "Example")` resolves successfully on
      this machine.
- [x] `idea_extensions.Example` schema (from this child's config wiring) makes `sheet_sync` a
      completed enum on `wt idea ext set --project Example ... sheet_sync <TAB>` (SPEC-0122).
- [x] No idea on this machine has `Ext Example.sheet_sync = yes` as a result of this child —
      the config wiring alone opts nothing in.
- [x] The skill's own procedure text never instructs `wt` to call a network tool itself —
      every Sheets read/write step names an MCP tool the *agent* calls, never `wt`.

## Test plan

- **Automated tests:** extended `tests/test_skills.py`'s `EXPECTED_SKILLS` with
  `wt-sheet-sync` — its existing `test_expected_skills_exist` /
  `test_frontmatter_has_name_and_description` / `test_thinness_references_help_not_flag_lists`
  parametrized checks all now cover the new skill (44 tests total, up from 41). No new code
  in this child, so no new test module.
- **Manual verification:** ran (this session, on this machine) `uv run wt sheet plan --project
  Example` → resolves the manifest and returns `{"push": [], "pull": []}` (nothing opted in yet,
  as expected); `extension_schema_for(load_config(), "Example")` returns the configured
  `sheet_sync`/`sheet_row`/`sheet_hash` schema.
- **Regression guard:** `uv run pytest` green (1088 passed); confirmed no existing idea's Ext
  state changed (the config wiring is opt-in-only, per Non-goals).

## Rollout / migration

Config/manifest changes are additive and machine-local (not committed to the repo — per
SPEC-0123's Decision, only the skill file is repo-versioned). Land after SPEC-0124/0125. Going
live against the real sheet is explicitly deferred (see Non-goals and SPEC-0123's Rollout).

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

(none — scope is fully determined by SPEC-0123's Architecture)

## What shipped / deviations

Implemented as designed: `skills/wt-sheet-sync/SKILL.md` (plan → MCP → record procedure,
column-ownership + scope guardrails, id-collision warning naming the sheet's known
`EXAMPLE-0002` duplicate); `~/.config/wt/schemes/example-pretriage-sheet.toml` (this machine);
`outbox_targets.Example.sheet` + `idea_extensions.Example` added to `~/.config/wt/config.yaml`.
One addition beyond the original Design: had to add `wt-sheet-sync` to
`tests/test_skills.py`'s `EXPECTED_SKILLS` allowlist (an existing SPEC-0017 guard against
undocumented skills) and add a `--help` pointer in the SKILL.md so it passed the existing
`test_thinness_references_help_not_flag_lists` check — not a new invariant, just satisfying
one this repo already enforces on every skill.
