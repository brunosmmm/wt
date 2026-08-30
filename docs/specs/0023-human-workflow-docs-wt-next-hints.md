---
id: SPEC-0023
title: Human workflow docs + wt next hints
status: done
owner: user
created: 2026-07-22
updated: 2026-07-22
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, ergonomics, docs, workflow]
source_idea: IDEA-010
depends_on: [SPEC-0017, SPEC-0022]
---

## Context

Promoted from idea `IDEA-010` (CLI + docs ergonomics so humans can memorize and run the
idea→spec→task workflow daily).

The [SPEC-0011](./0011-idea-to-spec-pipeline.md) pipeline and [SPEC-0017](./0017-agent-workflow-skills.md)
skills make the flow drivable for **agents**, but humans still struggle to memorize it:
`wt --help` reads like a time tracker, the root README barely mentions ideas→specs, and
`wt ideas` shows state without a **next action**. Accidents like `wt idea show …` (which
captures junk ideas — there is no `show` subcommand) are a symptom of that gap.

We want a durable human cheatsheet plus CLI affordances that answer “what do I do next?”
without opening skills or specs.

## Goals / Non-goals

**Goals**
- A one-page human cheatsheet at [`docs/WORKFLOW.md`](../WORKFLOW.md), linked from the root
  README and [`docs/README.md`](../README.md).
- `wt next` — print open ideas with the **next recommended command** for each.
- Enrich `wt ideas` with a **next** column (same rules as `wt next`).
- Keep WORKFLOW.md the source of truth for the card; updated when this CLI shipped.

**Non-goals**
- Replacing agent skills (`wt-new-work` et al.) — CLI hints complement them.
- Auto-running the next step (no `wt next --do`).
- A TUI/dashboard rewrite.
- Teaching the full spec-authxxing craft in the CLI (still SCHEMA.md / agent + human judgment).

## Decision

Ship (1) `docs/WORKFLOW.md` as the human pocket card, and (2) a small CLI surface: `wt next`
plus a `next` column on `wt ideas`, both driven by `workflow.next_step_for_idea`. Milestone:
M4 cli ergonomics (alongside [SPEC-0022](./0022-i-want-to-automatically-generate-comprehensive.md)).

## Design

### Docs

- [`docs/WORKFLOW.md`](../WORKFLOW.md) — pipeline card, idea-state table, commands, skills,
  ritual, fish abbrs, and `wt next` / `wt ideas` examples.
- Root README + `docs/README.md` link to it; README commands table lists `wt idea` /
  `wt ideas` / `wt next`.

### Next-step rules (`src/wt/workflow.py`)

`next_step_for_idea(cfg, idea) -> str`:

| Condition | Hint |
|-----------|------|
| DROPPED | `""` (omitted) |
| PROMOTED | `wt tasks` |
| no `:SPEC:` | `wt spec new --from-idea {id}` |
| linked spec missing | `spec {id} missing` |
| draft/proposed | `authxx {id} → accepted` |
| outbound + accepted/in-progress/done, not in PROVENANCE | `wt spec export {id}` |
| outbound already exported / internal done | `wt tasks` |
| internal accepted/in-progress | `wt spec generate {id}` |

### CLI

- `wt next [--all]` → `report.next_ideas` (open ideas; `--all` adds PROMOTED; DROPPED omitted).
- `wt ideas` → `next` column via the same helper.
- `wt idea --help` — “Capture only — list with `wt ideas`, next-step hints with `wt next`”.

## Alternatives considered

- **Docs-only** — rejected as the sole fix.
- **Only enrich `wt ideas`** — rejected; `wt next` is the memorable verb.
- **`wt workflow` that only prints WORKFLOW.md** — weaker than per-item next commands.

## Acceptance criteria

- [x] [`docs/WORKFLOW.md`](../WORKFLOW.md) exists and is linked from the root README and
      [`docs/README.md`](../README.md).
- [x] `wt next` lists open ideas with a next-command hint derived from shared rules.
- [x] `wt ideas` shows a `next` column consistent with `wt next` for the same idea.
- [x] `wt idea --help` states that it only captures and that listing is `wt ideas`.
- [x] Unit tests cover next-step mapping for IDEA (no spec), SPECCED+draft, SPECCED+accepted,
      PROMOTED, and soft-fail when the linked spec is missing (`tests/test_workflow.py`).
- [x] WORKFLOW.md documents `wt next` / `wt ideas` next column (replaced the planned note).
- [x] `uv run pytest` green (237 passed); no regression beyond the new column.

## Test plan

- **Automated:** `tests/test_workflow.py` — next_step cases + CliRunner for `wt next` /
  `wt ideas` / `wt idea --help`. Ideas tests updated for Rich 15 width (`_width`+`_height`).
- **Manual:** `uv run wt next` shows open ideas with hints; `wt idea --help` mentions
  capture-only. ✓
- **Regression:** `uv run pytest` → 237 passed; `python3 tools/spec_lint.py` OK.

## Rollout / migration

1. WORKFLOW.md + README links (docs).
2. `workflow.py` + `wt next` + `ideas` column + help tweak.
3. WORKFLOW.md examples refreshed; this spec marked done. No config migration.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest` → 237 passed); manual steps
      performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
