---
id: SPEC-0041
title: "Outbound idea lifecycle: EXPORTED handoff and portable build tracking"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
tags: [workflow, outbound, ideas, export, ergonomics]
source_idea: IDEA-032
depends_on: [SPEC-0014, SPEC-0015, SPEC-0023, SPEC-0033]
---

## Context

Promoted from `IDEA-032`.

After an accepted spec there are two handoff paths:

- **Internal:** `wt spec generate` → idea **PROMOTED** → build with local org tasks (`wt tasks`).
- **Outbound:** `wt spec export` → idea should become **EXPORTED** → build in the target repo.

Today only the internal path advances idea state. Export writes PROVENANCE and leaves the
idea **SPECCED**. `wt next` then says `wt tasks` once PROVENANCE exists — wrong for outbound
(no local tasks) and silent on whether the foreign agent started or finished.

Motivating miss: `IDEA-044` / `EXAMPLE-0001` exported into `example-ats`; next said `wt tasks`;
both outbox and portable copies stayed `accepted`; the implementing agent had only the
portable file + contract (no wt ledger).

## Goals / Non-goals

**Goals**
- Add idea state **EXPORTED** (done-side, sibling of PROMOTED — not the same thing).
- Successful `wt spec export` advances the linked idea SPECCED → EXPORTED.
- Treat the **portable spec in the target repo** as the working copy for build progress
  (`status` + AC checkboxes); foreign agents need no wt ledger.
- Optional command to mirror portable status back into the outbox (convenience, not a gate).
- `wt next` after EXPORTED points at implement / pull-status — never bare `wt tasks`.
- `wt spec generate` on outbound ids **refuses** (thin safety; fuller SpecRef is IDEA-031).

**Non-goals**
- Live sync / subscription between outbox and target.
- Product-fit / post-ship learning (IDEA-034 / IDEA-040).
- Full unified SpecRef module (IDEA-031) — only refuse non-`SPEC-` ids in generate.
- Making local org-task generate part of the outbound delivery path.
- New export schemes.

## Decision

Keep **PROMOTED** and **EXPORTED** as distinct done-side idea states. Internal handoff stays
`generate` → PROMOTED. Outbound handoff is `export` → EXPORTED (any scheme). Build progress
for outbound lives on the portable working copy; wt optionally pulls that status into the
outbox. Generate must not run on outbound ids.

## Design

### Idea keywords

Default `org_idea_keywords` (and the ideas.org `#+TODO` line):

```text
IDEA INCUBATE SPECCED | PROMOTED EXPORTED DROPPED
```

`EXPORTED` is done-side (hidden from default `wt ideas` open view, like PROMOTED).

### Export advances EXPORTED

On successful `wt spec export` (any scheme), if the outbound spec has `source_idea`, set that
idea to **EXPORTED** (same pattern as generate → PROMOTED in SPEC-0014). Idempotent if
already EXPORTED. Do not set PROMOTED.

### Portable working copy

wt-native portable frontmatter carries `status`. Contract text tells the foreign agent to
update `status` / AC on **this file**; optional `wt spec pull-status` mirrors back.

### Optional pull-status

`wt spec pull-status <outbound-id> [--to PATH]`:

1. Resolve outbox spec + configured (or `--to`) target path.
2. Read the portable spec (same filename under `spec_dir`).
3. Copy portable `status` (and `updated` if present) onto the outbox frontmatter; refresh
   outbox INDEX.
4. Soft-fail with a clear message if the portable file is missing.

### Re-export vs dest status

wt-native: when dest exists and content hash matches, preserve dest `status`/`updated`
unless `--force`. Divergent body still uses the existing non-clobber rules.

### `wt next` / `wt ideas` hints

For a linked outbound spec, after epic-extend checks (SPEC-0033):

| Idea / outbox situation | Hint |
|---|---|
| accepted/in-progress/done, not in PROVENANCE | `wt spec export {id}` |
| EXPORTED (or exported), outbox `accepted` | `implement in {target_repo}` |
| EXPORTED, outbox `in-progress` | `wt spec pull-status {id}` |
| EXPORTED, outbox `done` | quiet (empty string) |
| PROMOTED (internal) | `wt tasks` (unchanged) |

### Generate refuses outbound

`generate_from_spec` / `wt spec generate`: if the id is not `SPEC-…`, raise pointing at
`wt spec export`.

### Docs / skills

`docs/WORKFLOW.md`, `wt-orient`, `wt-export` updated for EXPORTED + portable working copy.

## Alternatives considered

- **Overload PROMOTED for export** — rejected; user lock.
- **Keep SPECCED + only change next hints** — rejected; triage still shows open design.
- **Require pull-status before done** — rejected; optional convenience.
- **Block on full SpecRef (IDEA-031)** — rejected; refuse-outbound is enough here.

## Acceptance criteria

- [x] Default idea keywords include done-side `EXPORTED` alongside `PROMOTED` / `DROPPED`.
- [x] Successful `wt spec export` for a spec with `source_idea` sets that idea to `EXPORTED`.
- [x] `wt next` / ideas next column never recommends `wt tasks` solely because an outbound
      spec was exported; hints follow the Design table.
- [x] `wt spec generate <outbound-id>` fails with an explicit message (no wrong internal tasks).
- [x] `wt spec pull-status <outbound-id>` mirrors portable `status` into the outbox when the
      dest file exists.
- [x] wt-native re-export with unchanged body preserves dest portable `status` unless
      `--force`.
- [x] WORKFLOW / export skill mention EXPORTED + portable working copy.

## Test plan

- **Automated:** `tests/test_workflow.py` (implement / pull-status / quiet hints);
  `tests/test_export.py` (EXPORTED advance, preserve status, pull-status, default keywords);
  `tests/test_generate.py` (outbound refuse). Executed: `uv run pytest` → 312 passed.
- **Manual:** ideas.org `#+TODO` updated; `wt next` for exported outbound no longer says
  `wt tasks`. Optional backfill: `wt state IDEA-044 EXPORTED` for pre-ship exports.
- **Regression:** Internal generate → PROMOTED and `wt tasks` unchanged; SPEC-0033 epic
  rework hints still win when Breakdown is open.

## Rollout / migration

1. Code + default config keywords shipped.
2. `~/work/org/ai/ideas.org` `#+TODO` includes `EXPORTED`.
3. Optional backfill for already-exported SPECCED ideas (e.g. IDEA-044):
   `wt state IDEA-044 EXPORTED`.
4. No change to already-exported portable files until next pull/re-export.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green; ledger regenerated.
- [x] Spec body matches what shipped.

## Open questions

_None._
