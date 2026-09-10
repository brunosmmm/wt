---
id: SPEC-0123
title: "Google Sheets sync scheme: push/pull wt ideas <-> a project's thin backlog"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
source_idea: IDEA-200
kind: epic
milestone: "M7: sheet sync"
tags: [ideas, sync, sheets, extensions]
# depends_on: []
---

## Context

Promoted from idea `IDEA-200` (Google Sheets sync scheme: push/pull wt ideas <-> a project's thin triage backlog).

  :PROPERTIES:
  :ID: IDEA-200
  :CREATED: [2026-08-04 Tue 16:29]
  :UPDATED: [2026-08-04 Tue 17:11]
  :PROJECT: Meta-Tools
  :KIND: idea
  :EXPLORED: 1
  :EXPLORED_AT: [2026-08-04 Tue 17:06]
  :END:
** Summary
A generic, portable sync between wt's **idea** stage (loose capture) and an external
project's thin, external triage backlog living in a Google Sheet. First concrete target:
Example's "Pre-triage Backlog" tab (spreadsheet 1JFGArwv8QoWwQRushxjkV7tbd8nxp465sWg1Q5tPXLs).
`Example` is already a configured project (~/.config/wt/config.yaml outbox_targets.Example,
repo_path ~/work/example-ats) and its proj-code `EXAMPLE` already matches the `EXAMPLE-NNNN` ids
already sitting in that sheet.

Explicitly **not** in scope: the separate "ATS Product Requirements (PRD Tracker)" spreadsheet
(its own `Features`/`Schema` tabs, PFW-ATS-NNN ids). That sheet is a stricter,
requirements-only artifact (declarative, present-tense, no implementation odds-and-ends,
design notes explicitly relegated to a side Notes field) and does not match the looseness of
a wt idea (which can hold implementation details, half-formed decisions, exploration notes).
Ruled out after discussion — do not conflate idea-sync with spec/PRD-sync.

Where the schema/config should live (by analogy with SPEC-0058's user-config-dir export
schemes, e.g. ~/.config/wt/schemes/REMOVED-extended.toml):
- **Mechanism** (code that reads a manifest + does row upserts via the Sheets API) — in-tree in
  wt, a new sibling to `src/wt/export_schemes/` (generic/portable, ships with wt).
- **Manifest** (this sheet's actual column mapping) — NOT committed to wt's repo; lives in
  `~/.config/wt/schemes/` (e.g. a new `example-pretriage-sheet.toml`), since it's specific to
  this one external sheet, same reasoning as the extended REMOVED example manifest already
  living there rather than in-tree.
- **Connection details** (spreadsheet_id, tab, which manifest to use) — a new key under
  `outbox_targets.Example` in `~/.config/wt/config.yaml`, alongside the existing
  `repo_path`/`spec_dir`.
- Optional: a self-describing `Schema` tab inside the sheet itself (the PRD tracker already
  does this) as human-readable documentation — not the enforced source of truth; wt's own
  manifest stays authxxitative.

Sync model (reusing the hash-based reconciliation pattern SPEC-0041/0064/0067 already built
for outbound markdown specs, not inventing a new one): asymmetric column ownership. wt owns
content columns (e.g. Feature/title, derived from the idea); the sheet/human owns triage-only
columns (e.g. Costumer, and whatever triage state gets added). On-demand CLI push/pull
(`wt sheet push/pull`, working name), no live/webhook sync — consistent with wt's existing
file-drop-only philosophy (no live orchestration elsewhere either). Push scope is filtered by
the existing `:PROJECT:` property (`wt ideas --project Example`), which already answers "don't
push every idea from every project into Example's sheet."

Known live issue in the current sheet (ignore for schema design, but must be fixed before any
sync go-live): `EXAMPLE-0002` is used for two different rows already — ids are not yet a
reliable join key.
** Open questions
*** RESOLVED Exact thin column set beyond ID/Feature/Costumer -- add Status/Priority driven by wt's :PRIORITY:/state, or keep it purely a mirror of what's there today?
Resolved: add a Status column. wt-owned (push-only) -- a coarse mirror of the idea's own lifecycle (e.g. derived from state/:PRIORITY: and whether a spec exists yet), same content/triage-column split as Feature: wt is the source of truth for idea lifecycle, the sheet just displays it. Costumer stays the sheet/human-owned column, unchanged.
*** RESOLVED ID join key: reuse the existing outbound-style PROJ-NNNN allocator (next_outbound_number) for sheet rows, or a separate counter scoped to the sheet?
Resolved leaning: mint sheet-row ids the same way next_outbound_number scans a directory for max <PROJ>-NNNN, but scan the sheet's own ID column instead of a filesystem glob. Residual risk found in the wild: the Pre-triage Backlog already has a duplicate EXAMPLE-0002, and Example's outbound docs/specs counter (outbox_targets.Example) mints the same EXAMPLE- prefix independently -- these are two uncoordinated counters sharing one prefix today. Follow-up decision needed at design time: keep them deliberately separate (sheet ids are pre-triage, never promoted 1:1 into EXAMPLE-NNNN spec ids) or reconcile into one counter.
*** RESOLVED Conflict handling when both wt and a human edit a wt-owned content column since the last sync -- hard refuse like _write_owned's non-clobber guard, or something softer?
Resolved: reuse export.py's exact _write_owned non-clobber contract (write if absent, no-op if byte-identical, refuse a divergent overwrite without --force) for wt-owned columns. No new conflict model needed -- SPEC-0016 already established this precedent for exactly this shape of problem.
*** RESOLVED Manifest format: TOML like TemplateScheme's declarative markdown manifests, or a new shape suited to spreadsheet columns instead of markdown sections?
Resolved: TOML, mirroring TemplateScheme's manifest tier (export_schemes/template_scheme.py) but flat instead of sectioned -- a sheet manifest is name/description/required_fields/columns:[{header, source, owner: wt|sheet}] rather than sections:[{label, source}], since spreadsheet rows have no prose sections to interleave. Lives in ~/.config/wt/schemes/ per SPEC-0058 precedent (this idea's Summary), loaded the same way load_manifests_from() already loads user manifests -- new loader, same shape.
*** RESOLVED Auth/credentials story for calling the Sheets API from wt's own CLI context (service account vs OAuth) -- unexplored.
Resolved -- hard constraint, not a preference: wt's own CLI process has no path to call the Sheets API at all; the only thing with Google access is the driving agent's session (Claude Code + the Google Sheets MCP tools), and that's a per-conversation capability, not something wt-the-program can carry credentials for. This throws out 'wt sheet push/pull calls the Sheets API directly' (revise Q6's design accordingly): wt must stay transport-agnostic. wt's job is to compute a sync plan (which ideas to push, which sheet rows to pull) and emit/accept it as JSON; the actual Sheets reads/writes are performed by whatever agent is driving, via its own MCP tools, then reported back to wt to persist bookkeeping (sheet_row/sheet_hash via Ext).
*** RESOLVED Surface as a new /wt-sheet-sync skill + wt sheet push/pull commands, or fold into the existing wt-export skill/CLI surface?
Revised (supersedes the original push/pull framing after Q5): wt itself never touches the Sheets API. wt exposes JSON-only primitives -- e.g. wt sheet plan --json (diff: which :PROJECT: Example ideas with Ext sheet_sync=yes need pushing, keyed against stored sheet_row/sheet_hash) and wt sheet record --json (persist row id + new hash back onto the idea's Ext after an agent actually writes/reads the sheet). A /wt-sheet-sync skill orchestrates: call wt for the plan, call the Google Sheets MCP tools to apply it, call wt to record the result. Kept as its own skill/command group, still separate from wt spec export's file-drop contract.
*** RESOLVED Ext key design for sync inclusion/exclusion + bookkeeping: single boolean-ish key (e.g. sheet_sync) plus separate sheet_row_id/sheet_synced_hash keys under Ext Example, or one structured value -- and does this need a schema entry in idea_extensions.Example (required vs optional) to be write-enforced?
Resolved (design sketch): Ext Example gets sheet_sync (enum: yes/no, optional -- absence means not synced, so existing ideas are unaffected), plus two bookkeeping keys sheet_row (the sheet row's EXAMPLE-NNNN id) and sheet_hash (content hash at last push/pull, for the _write_owned-style conflict check in Q3). All three declared as optional properties (not required) in idea_extensions.Example, so an idea can carry a :PROJECT: Example without being forced to decide sheet_sync at capture time (epic's own non-goal: 'required at capture' rejected).
** Log
*** [2026-08-04 Tue 16:30]
Considered mapping wt's spec stage to the separate ATS Product Requirements (PRD Tracker) spreadsheet (its own Schema tab, PFW-ATS-NNN ids). Rejected: the PRD is a stricter requirements-only artifact and doesn't match a wt idea's looseness (implementation details, decisions, odds and ends are fine in an idea, not in that PRD). Scope narrowed to idea-stage sync against Example's thinner Pre-triage Backlog tab only.
*** [2026-08-04 Tue 17:03]
Discovered wt's new project-namespaced idea extensions (SPEC-0118/0119/0120/0121/0122, uncommitted on this branch): per-idea `** Ext <Project>` org drawer + JSON extensions map, optional per-project schema in config.yaml's idea_extensions: (required/optional keys, string|enum types), enforced at write time, full CLI via `wt idea ext show|set|clear|list|lint`. This directly answers open question 1 and adds a new mechanism: use an Ext key under Ext Example (e.g. sheet_sync: yes/no, or an enum) as the per-idea include/exclude signal for sheet sync -- finer-grained than the existing :PROJECT: filter alone, and itself project-private (wt core need not know what it means). Also a candidate home for sync bookkeeping state (e.g. sheet_row_id, sheet_synced_hash) instead of a separate wt-data-dir sync-state file, since Ext is exactly 'project-private state wt's core workflow does not own.'
*** [2026-08-04 Tue 17:06]
Explore pass: read export_schemes/**init**.py (OutputFile mode contract: native-spec/contract/owned/splice), template_scheme.py (manifest tier + SPEC-0058 user-config-dir loader), extension_schema.py (idea_extensions normalize/validate), and pyproject.toml (wt has zero network/HTTP deps today -- click/rich/pyyaml/orgparse/optional textual only). Resolved 5 of 7 open questions with concrete leanings (see question rationale bodies): ID minting (with a flagged residual counter-collision risk between sheet ids and Example's outbound docs/specs counter), conflict handling (reuse _write_owned verbatim), manifest format (TOML, flat TemplateScheme sibling), CLI/skill surface (new wt sheet push|pull + /wt-sheet-sync, kept separate from wt spec export's file-drop contract), and the Ext key design (sheet_sync/sheet_row/sheet_hash, all optional). Left open: exact thin column set (product judgment call) and Sheets API auth story (service account vs OAuth -- genuinely unexplored, first network dependency this tool would take on, needs an org/IT decision not a code answer).
*** [2026-08-04 Tue 17:11]
Key architecture correction from the human: wt's CLI process cannot call the Sheets API at all -- only the driving agent session (here, via the Google Sheets MCP tools) has that access. This kills the earlier 'wt sheet push/pull calls Sheets directly' framing (Q6) and reshapes the design: wt exposes JSON-only sync primitives (a plan to push/pull, a record call to persist bookkeeping); a /wt-sheet-sync skill is what actually drives the Sheets MCP calls in between. Also resolved: Status column is worth adding, wt-owned/push-only, mirroring idea lifecycle; Costumer remains sheet/human-owned.

## Goals / Non-goals

**Goals**
- A generic, portable mechanism for syncing wt's **idea** stage against a thin, external
  triage backlog living in a Google Sheet, keyed by project (`:PROJECT:`), not hardcoded to
  Example — Example's "Pre-triage Backlog" tab is the first concrete instance, not the design
  target.
- A per-sheet column-mapping manifest (TOML, user-config-dir, not committed to wt's own repo)
  declaring which columns wt owns (pushes) vs which the sheet/human owns (never overwritten).
- Per-idea opt-in/out and sync bookkeeping stored as project Ext (SPEC-0118/0119/0122)
  (`sheet_sync`, `sheet_row`, `sheet_hash` under `Ext <Project>`) — not a new global sync-state
  file, not a required field at capture.
- wt stays transport-agnostic: it computes/consumes a JSON sync plan and records results;
  it never calls the Sheets API itself (see Context — this is a hard constraint, not a style
  choice).
- A `/wt-sheet-sync` skill that drives the actual Sheets reads/writes (via the operator's own
  Google Sheets MCP tools) between wt's plan and wt's record.

**Non-goals**
- Syncing wt's **spec** stage against any PRD-shaped sheet (e.g. the separate "ATS Product
  Requirements (PRD Tracker)" spreadsheet). That's a stricter, requirements-only artifact and
  does not match a wt idea's looseness — explicitly ruled out during explore (IDEA-200 Log).
- Live/webhook sync of any kind. On-demand only, consistent with wt's existing file-drop-only
  philosophy (SPEC-0015's export Non-goals) — a sync run is something an agent or human
  triggers, not something that watches either side continuously.
- `wt` itself holding or managing Google credentials. No new network/HTTP dependency is added
  to `wt`'s own `pyproject.toml`.
- Free-form bidirectional field-level merge. Column ownership is a fixed, declared split per
  manifest — never a per-field negotiation at sync time.
- Reconciling the Pre-triage Backlog sheet's pre-existing duplicate `EXAMPLE-0002` id, or any
  other cleanup of that sheet's current contents — that's operational, not part of this
  design (flagged in IDEA-200, out of scope here).

## Decision

Ship an epic whose contract is:

1. **Manifest + config** (child 1): a TOML column-mapping manifest — sibling to
   `export_schemes/template_scheme.py`'s declarative tier, but flat (columns, not sections) —
   loaded from `<config_dir>/schemes/` (SPEC-0058 precedent), plus a new
   `outbox_targets[project].sheet` config key (`spreadsheet_id`, `tab`, `manifest`).
2. **Plan/record CLI** (child 2): `wt sheet plan --project <P> --json` computes the sync diff
   (which ideas need pushing, which sheet rows — by id — need pulling) against each idea's
   `Ext <P>` bookkeeping (`sheet_row`/`sheet_hash`), applying the manifest's column-ownership
   split and an `_write_owned`-style hash conflict check (SPEC-0016 precedent, reused, not
   reinvented). `wt sheet record --project <P> --json` takes a completed sync's results back
   in and persists them onto the relevant ideas' Ext via the existing `idea_ext` mutators.
   Neither command touches the network.
3. **Skill + reference instance** (child 3): `/wt-sheet-sync` orchestrates
   `wt sheet plan` → Google Sheets MCP calls → `wt sheet record`, and ships the first real
   manifest (`example-pretriage-sheet.toml`) plus the Example `outbox_targets`/`idea_extensions`
   config wiring as the reference example other projects copy.

## Architecture / cross-cutting design

```
idea (:PROJECT: P, Ext P {sheet_sync, sheet_row, sheet_hash})
        |
        v
config: outbox_targets[P].sheet {spreadsheet_id, tab, manifest}
        |
        v
manifest: <config_dir>/schemes/<manifest>.toml
   name / description / columns: [{header, source, owner: wt|sheet}]
        |
        v
wt sheet plan --project P --json  -->  {push: [...], pull: [...]}
        |                                   ^
        v                                   |
  (driving agent's Google Sheets MCP calls, outside wt) ------+
        |
        v
wt sheet record --project P --json  -->  writes Ext sheet_row/sheet_hash
```

**Invariants**
- `wt` never performs a Sheets API call, directly or via a library dependency — plan/record
  are pure JSON in/out over the local idea corpus + manifest. This is what makes the
  auth question (IDEA-200 Q5) moot for `wt` itself: whatever agent drives the skill supplies
  its own Sheets access.
- Column ownership is declared once, in the manifest, as `owner: wt` (wt is the source of
  truth; a divergent sheet-side edit to a wt-owned column is a conflict, refused without an
  explicit override — same shape as `export.py`'s `_write_owned`) or `owner: sheet` (human/
  sheet is the source of truth; wt only reads it back on `record`, never pushes it).
  `sheet_hash` is computed over the wt-owned columns' rendered values only.
  Column ownership is a manifest-level policy — child 2 provides one path per owner value,
  not a per-run negotiation.
- Sync scope is always `ideas where :PROJECT: == P and Ext P.sheet_sync == "yes"` — both the
  existing project filter and the new Ext opt-in must hold; there is no "sync everything in
  project P" mode.
- No schema for a project's Ext ⇒ `sheet_sync`/`sheet_row`/`sheet_hash` are still legal
  freeform Ext keys (SPEC-0118 invariant); a project that wants CLI enum completion for
  `sheet_sync` declares it in `idea_extensions[P].properties` (optional, not required —
  SPEC-0118 Non-goal: no required-at-capture).
- One id space per project (`<PROJ>-NNNN`, e.g. `EXAMPLE-NNNN`) is assumed shared between the
  sheet and wt's existing outbound spec ids for that project; child 2's id allocator must
  scan the sheet's own id column for the current max (mirroring
  `specs.next_outbound_number`'s directory scan) — see the residual collision risk recorded
  on IDEA-200 (the sheet already has a duplicate `EXAMPLE-0002`, and the outbound `docs/specs`
  counter for the same prefix runs independently). Child 2 documents this risk; it does not
  need to solve cross-counter reconciliation to be done.

## Breakdown / sub-specs

- [x] SPEC-0124 (project: Meta-Tools) — Sheet-sync manifest format + `outbox_targets[project].sheet` config
- [x] SPEC-0125 (project: Meta-Tools) — `wt sheet plan`/`wt sheet record` JSON CLI (depends_on SPEC-0124)
- [x] SPEC-0126 (project: Meta-Tools) — `/wt-sheet-sync` skill + Example reference manifest/config (depends_on SPEC-0124, SPEC-0125)

Sequencing: 0124 → 0125 → 0126, strictly serial — each child's contract is the input the next
one needs (manifest shape before plan/record can read one; plan/record before the skill has
anything to orchestrate). No parallel work across children.

## Acceptance criteria

- [x] A project can declare a sheet-sync target (`outbox_targets[P].sheet` + a manifest under
      `<config_dir>/schemes/`) with zero code changes to `wt`.
- [x] `wt sheet plan --project Example` lists exactly the ideas with `:PROJECT: Example`
      and `Ext Example.sheet_sync = yes` that need pushing (new or changed since last recorded
      `sheet_hash`), and (given `--sheet-rows`) any unknown sheet rows to pull, without making
      any network call.
- [x] The mechanism end-to-end (push → record → clean re-plan; adopt → new idea with Ext set)
      is verified against fixtures and against this machine's real Example manifest/config
      (`test_cli_sheet_plan_and_record`, plus a live `wt sheet plan --project Example` run —
      see Test plan). A run against the *live* Pre-triage Backlog sheet itself is deliberately
      **not** part of this epic's DoD — Rollout below gates that on fixing the sheet's
      existing duplicate `EXAMPLE-0002` id first, which is out of scope here.
- [x] A divergent edit to a wt-owned column is detected: `plan_push`'s hash comparison flags
      `action: "update"` whenever an idea's rendered content no longer matches the stored
      `sheet_hash` (`test_plan_push_skips_unchanged_and_flags_stale`); resolving it is a
      human/skill decision (SPEC-0125 Non-goals), not automatic.
- [x] `grep` of `pyproject.toml` shows no new runtime dependency added for this epic — `wt`
      itself stays network-free (verified: only `click`/`rich`/`pyyaml`/`orgparse` +
      optional `textual`, unchanged).
- [x] All child specs `done` or `superseded`.

## Test plan

- **Integration/e2e tests:** `tests/test_sheet_sync.py` (9) + `tests/test_sheet_schemes.py`
  (12) — a fixture manifest + fixture ideas corpus exercising `wt sheet plan`/`wt sheet
  record` end-to-end (push-new, push-update-after-change, skip-unchanged, pull-unknown-row,
  record-pushed, record-adopted, CLI round-trip via `CliRunner`) without any real network call
  — the Sheets side is simulated as plain JSON fixtures matching what the MCP tools would
  return/accept, since `wt` never calls the API directly.
- **Manual verification:** ran `wt sheet plan --project Example` on this machine against the
  real reference manifest/config (SPEC-0126) — resolved cleanly, returned an empty plan
  (correct: no idea has opted in yet). Did **not** run `/wt-sheet-sync` against the live
  Pre-triage Backlog sheet — deferred per Rollout below.
- **Regression guard:** `uv run pytest` green (1090 passed); existing idea/Ext/export-scheme
  tests unaffected; `python3 tools/spec_lint.py` exit 0.

## Rollout / sequencing

Land 0124 → 0125 → 0126 in order; each is independently mergeable but only 0126 is
user-visible end-to-end. Do not point `/wt-sheet-sync` at the live Example Pre-triage Backlog
sheet until: (a) its existing duplicate `EXAMPLE-0002` id is fixed by hand, and (b) a manual
dry run against a disposable copy/tab has been verified clean. This epic's Definition of Done
does not require the live sheet to have been synced — only that the mechanism works against a
verified fixture/disposable target.

## Definition of done

- [x] All child specs `done` or `superseded` (the linter gates this).
- [x] Integration test plan executed; `uv run pytest` green.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

(none — resolved on IDEA-200 before accept; see that idea's Open questions section for the
full rationale behind each design decision above)

## What shipped / deviations

Implemented as designed across SPEC-0124/0125/0126: `src/wt/sheet_schemes.py` (manifest
model + config resolution), `src/wt/sheet_sync.py` + `wt sheet plan`/`wt sheet record` (JSON
diff/record, no network), `skills/wt-sheet-sync/SKILL.md` (orchestration procedure), and the
Example reference manifest/config on this machine. One Architecture deviation worth recording:
the Architecture section above describes "child 2's id allocator... scan the sheet's own id
column for the current max" — in practice, `plan_push`/`record` (SPEC-0125) never mint ids at
all; a new row's id is assigned by whoever actually writes it into the sheet (the driving
agent, per the `/wt-sheet-sync` skill's step 4), and `wt sheet record` only stores whatever id
it's told. This is simpler than an in-wt allocator and sidesteps the counter-collision risk
more cleanly (the agent doing the write is also the one positioned to check the sheet's
current ids for collisions at write time) — no code needed to change, since `wt` was already
transport-agnostic; SPEC-0125's own Non-goals already documented this choice.

Deliberately not done (by design, not oversight): no idea has been opted into sheet-sync, and
no sync has run against the live Pre-triage Backlog. Going live is gated on fixing that
sheet's existing duplicate `EXAMPLE-0002` id and a disposable-tab dry run — an operational
follow-up, not a code gap.
