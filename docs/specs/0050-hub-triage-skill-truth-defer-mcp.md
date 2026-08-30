---
id: SPEC-0050
title: "Hub triage, skill truth, defer MCP"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: epic
tags: [skills, hub, mcp, workflow-audit, ergonomics]
source_idea: IDEA-058
depends_on: [SPEC-0017, SPEC-0021, SPEC-0026, SPEC-0041, SPEC-0045]
---

## Context

Promoted from `IDEA-058`. Agents need (1) a single triage view across ledger-worthy
internal work, data-dir outbound, and org ideas without stuffing outbound into git
`LEDGER.md`; (2) skills that match CLI hard rules; (3) a clear decision on optional MCP
now that `--json` exists for the idea path.

## Goals / Non-goals

**Goals**
- Honest skills/help; a read-only hub JSON command; explicit MCP deferral policy.

**Non-goals**
- Changing ledger generation to include outbound.
- Shipping an MCP server in this epic’s children (deferred by SPEC-0053).

## Decision

Three children under this epic:

1. **SPEC-0051** — Align skills + CLI help with post-0021/0041 reality.
2. **SPEC-0052** — `wt hub --json` (`wt.hub.v1`) composing ideas + internal + outbound.
3. **SPEC-0053** — Policy: defer MCP until hub/`--json` prove insufficient.

## Architecture / cross-cutting design

- **Ledger stays internal-only** (`tools/spec_lint.py --write-ledger`). Hub must not write it.
- **Outbox stays data-dir** (`outbox_dir(cfg)`).
- **Agent reads:** prefer structured JSON (`SPEC-0026`, hub) over scraping Rich.
- **Skills → CLI/library**; MCP (if ever) wraps the same helpers, never a second business layer.

## Breakdown / sub-specs

- [x] [SPEC-0051](./0051-align-skills-and-help-with-cli-reality.md) — Skill/help truth (`done`)
- [x] [SPEC-0052](./0052-wt-hub-json-triage-across-ideas-specs-outbox.md) — `wt hub --json` (`done`)
- [x] [SPEC-0053](./0053-defer-optional-wt-mcp-server.md) — Defer MCP (policy) (`done`)

Implement **0051 → 0052**; **0053** is docs-only when accepted.

## Acceptance criteria

- [x] All three children `accepted` with `parent: SPEC-0050`.
- [x] Epic open until children `done`/`superseded`.

## Test plan

Integration via children. Hub must not mutate `docs/LEDGER.md`. Skills grep-guards green.

## Rollout / sequencing

1. Accept epic + children.
2. Implement 0051 then 0052; close 0053 as policy (no code).
3. Mark epic done when children done.

## Definition of done

- [x] Children done/superseded; ledger current.

## Open questions

_None._
