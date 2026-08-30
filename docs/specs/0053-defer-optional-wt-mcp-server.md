---
id: SPEC-0053
title: "Defer optional wt MCP server"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: policy
parent: SPEC-0050
tags: [mcp, skills, policy]
source_idea: IDEA-015
depends_on: [SPEC-0017, SPEC-0026, SPEC-0052]
---

## Context

Promoted from `IDEA-015` (epic SPEC-0050). SPEC-0017 deferred MCP so skills + CLI stay the
surface. SPEC-0026 shipped `--json` for ideas/next/show. IDEA-015’s explore left “worth it?”
open; pyproject has no MCP extra today.

## Goals / Non-goals

**Goals**
- Record an explicit **defer** decision with revisit criteria.
- Sketch the packaging/tool shape if MCP is revived later (so we don’t re-debate from zero).

**Non-goals**
- Implementing an MCP server in this spec.
- Expanding `--json` to topics/report (separate idea if needed).

## Decision

**Do not ship** a wt MCP server in this milestone. Agent workflow remains:

`skills → wt CLI (--json where present) → same Python library`.

Revisit MCP only if, after SPEC-0052 `wt hub --json` is in use, agents still need typed
tool discovery or write APIs that shell+JSON cannot cover cleanly.

## Design (deferred sketch — not to implement now)

If revived:

| Lock | Choice |
|------|--------|
| Packaging | Optional `wt[mcp]` extra; core deps unchanged |
| Entry | `wt mcp serve` or console script |
| v1 tools | Thin wrappers: ideas list/next/show; optional idea capture/log/summary |
| Exclude | Full CLI mirror, ledger writes, meetings, map/override |

## Alternatives considered

- **Ship MCP now** — rejected; `--json` + hub cover the stated agent read gap;
  second surface risks drift.
- **Never MCP** — too absolute; leave revisit door open.

## Acceptance criteria

- [x] This policy is accepted/done and referenced from epic SPEC-0050.
- [x] No MCP dependency added to `pyproject.toml` by this work.
- [x] IDEA-015 Log/Summary reflect defer (see idea Log); policy tasks are documentation only.
- [x] WORKFLOW or `wt-orient` one-liner: MCP deferred; use `--json` / `wt hub`.

## Test plan

- **Automated:** `tests/test_mcp_deferred.py` asserts no mcp extra / no `src/wt/mcp*` — green.
- **Manual:** Confirmed no MCP module introduced.
- **Regression:** skills install / `--json` paths unchanged.

## Rollout / migration

None. When revisiting, open a **new** feature spec that supersedes or depends on this policy.

## Definition of done

- [x] Policy done; docs mention deferral; no MCP code shipped under this id.

## Open questions

_None._
