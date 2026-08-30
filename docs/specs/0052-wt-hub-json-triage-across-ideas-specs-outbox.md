---
id: SPEC-0052
title: "wt hub JSON triage across ideas, specs, and outbox"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
parent: SPEC-0050
tags: [cli, json, hub, outbound, ergonomics]
source_idea: IDEA-039
depends_on: [SPEC-0021, SPEC-0026, SPEC-0051]
---

## Context

Promoted from `IDEA-039` (epic SPEC-0050). In-flight work spans git ledger (internal),
data-dir outbox INDEX (outbound), and org ideas. Agents currently juggle three reads.
Outbound must stay out of `docs/LEDGER.md`.

## Goals / Non-goals

**Goals**
- `wt hub --json` → `wt.hub.v1` union payload for triage.
- Reuse existing collectors; zero writes to ledger.

**Non-goals**
- Writing a git-tracked hub file or extending `write_ledger` to outbound.
- Rich table in v1 (optional follow-up).
- Mutating commands or replacing `wt ideas` / `wt next`.

## Decision

Add read-only `wt hub` with required `--json` in v1. Payload composes three arrays from
existing seams.

## Design

### Schema `wt.hub.v1`
```json
{
  "schema": "wt.hub.v1",
  "ideas": [ /* idea_row open ideas */ ],
  "internal": [
    {"id", "title", "kind", "status", "milestone", "updated", "parent?"}
  ],
  "outbound": [
    {"id", "title", "kind", "status", "project", "target_repo", "updated", "path?"}
  ]
}
```

### Implementation
- `report.hub_payload(cfg)` / `report.hub`:
  - `ideas` ← `collect_idea_rows(cfg, all_done=False)`
  - `internal` ← scan `cfg["specs_dir"]` `[0-9]*.md` via `split_frontmatter`; include statuses
    in `{draft, proposed, accepted, in-progress}` (exclude done/superseded/rejected)
  - `outbound` ← `_outbound_specs(cfg)` / INDEX-equivalent fields
- CLI: `wt hub --json` (UsageError without `--json` in v1).
- **Never** call `write_ledger` / mutate `LEDGER.md`.

### Skills
- `wt-orient` / WORKFLOW: triage via `wt hub --json`.

## Alternatives considered

- **Agent composes three commands** — status quo; IDEA asks for one surface.
- **Data-dir hub.json file** — deferred; stdout is enough.
- **Org-only board** — incomplete.

## Acceptance criteria

- [x] `wt hub --json` emits `wt.hub.v1` with `ideas`, `internal`, `outbound`.
- [x] Running hub does not modify `docs/LEDGER.md`.
- [x] Internal list omits done/superseded/rejected; ideas match open `wt ideas --json`.
- [x] Outbound rows reflect data-dir outbox (empty arrays OK when none).
- [x] Tests cover fixture with idea + internal draft + outbound stub.
- [x] WORKFLOW or `wt-orient` mentions hub.

## Test plan

- **Automated:** `tests/test_hub.py` — **executed, green**.
- **Manual:** `wt hub --json` from wt repo; confirmed no ledger diff.
- **Regression:** ideas/next JSON unchanged; full suite green.

## Rollout / migration

None.

## Definition of done

- [x] AC met; tests green; ledger updated.

## Open questions

_None._
