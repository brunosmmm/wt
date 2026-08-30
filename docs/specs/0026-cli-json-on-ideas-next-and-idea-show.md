---
id: SPEC-0026
title: "CLI --json on ideas, next, and idea show"
status: done
owner: user
created: 2026-07-22
updated: 2026-07-22
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, agents, ergonomics, json]
source_idea: IDEA-016
depends_on: [SPEC-0012, SPEC-0023, SPEC-0024]
---

## Context

Promoted from idea `IDEA-016`.

Agents drive the idea→spec workflow via shell (`wt ideas`, `wt next`, `wt idea show`) but
those commands were **Rich-print-only**. Scraping tables is brittle. Structured **stdout
JSON** on the three reads agents already use is the cheap alternative to an MCP
(IDEA-015). `wt export --format json` remains a file export of time rows — unchanged.

## Goals / Non-goals

**Goals**
- `--json` on `wt ideas`, `wt next`, and `wt idea show <id>` emitting versioned JSON on
  stdout.
- Shared row/payload builders; Rich printers consume the same data.
- Default (no flag) behavior unchanged for humans.

**Non-goals**
- `--json` on `topics` / `report` / `tasks` / `digest`.
- Changing `wt export --format json`.
- MCP (IDEA-015).
- `file` / `line` in v1 payloads.
- Dual-writing Rich + JSON in one invocation.

## Decision

Ship `--json` on the three idea-workflow read commands only. When set, print a versioned
JSON envelope to stdout and skip Rich. Schemas: `wt.ideas.v1`, `wt.next.v1`, `wt.idea.v1`.
Omit empty optional `project`/`spec`; `tags` always an array; list rows always include
`next`.

## Design

### Shipped

- `report.idea_row` / `collect_idea_tasks` / `collect_next_tasks`; `ideas`/`next_ideas`
  take `as_json=`.
- `explore.idea_show_payload` / `dump_idea_show_json`; `format_idea_show` uses the payload.
- CLI `--json` on `ideas`, `next`, `idea show`.
- `docs/WORKFLOW.md` one-liner; help text on the three commands.
- Tests: `tests/test_json_cli.py`.

### Envelopes

`{"schema":"wt.ideas.v1","ideas":[…]}`, `wt.next.v1` same row shape, `wt.idea.v1` with
summary/questions/log. indent=2 on stdout.

## Alternatives considered

As accepted: MCP deferred; topics/report JSON deferred; export untouched; always-JSON
rejected.

## Acceptance criteria

- [x] `wt ideas --json` prints `wt.ideas.v1` envelope to stdout; no Rich table.
- [x] `wt next --json` prints `wt.next.v1` envelope; rows include `next`.
- [x] `wt idea show <id> --json` prints `wt.idea.v1` with summary/questions/log.
- [x] Without `--json`, existing Rich/text output is unchanged.
- [x] Shared builders: Rich and JSON paths share filter/next-step via `idea_row`.
- [x] Automated tests in `tests/test_json_cli.py`; full suite green.
- [x] Help text documents `--json`; WORKFLOW mentions it.

## Test plan

- **Automated:** `tests/test_json_cli.py` — schema, fields, Rich default. ✓
- **Manual:** `wt ideas --json | python -m json.tool` (+ next / idea show). ✓
- **Regression:** full `uv run pytest`. ✓

## Rollout / migration

Shipped behind `--json`. No data migration.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

_None._
