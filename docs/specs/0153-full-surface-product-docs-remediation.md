---
id: SPEC-0153
title: "Full-surface product docs remediation"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: epic
tags: [docs]
depends_on: [SPEC-0148]
source_idea: IDEA-390
---

## Context

SPEC-0148 shipped ideas-desk SVG captures, Mermaid workflows, and an org-storage guide.
A ten-persona audit against `docs/product/`, the live CLI, and anonymized local usage
still found the site underselling wt: time suite invisible, guides pipeline-shaped not
day-shaped, architecture/agent/outbound depth thin.

Promoted from `IDEA-390`.

## Goals / Non-goals

**Goals**

- Deterministic demo fixture covering **time + tasks + ideas** (not ideas alone).
- Wave A/B/C SVG captures for the surfaces auditors called fatal omissions.
- Journey pages: home + getting-started forks + daily/weekly operating guides.
- Architecture + lifecycle teaching (topology, states, project identity, DoD matrix).
- Agent surface guide (schemas, skill→CLI, JSON recipes).
- Outbound/multi-project depth with close-the-loop as required narrative ops.

**Non-goals**

- Team RACI / squad governance playbook (separate later).
- Deep sheet-sync productization.
- Switching diagram DSL from Mermaid to D2.
- Checking live contributor XDG corpora into git.

## Decision

Ship a **new epic** after SPEC-0148 rather than reopening finished children. Five feature
children in priority order; child 1 (fixture + Waves A/B) unblocks everything visual.
Journey rewrite embeds those shots so the first viewport sells the dual product.
Architecture, agent, and outbound children can fan out after captures exist; Wave C lives
with the outbound child.

Fold SPEC-0148's leftover "capability page embeds" into the journey child rather than
keeping 0148 open indefinitely.

## Architecture / cross-cutting design

```
scripts/docs-capture.py
  → tmp demo cfg
  → seed ideas + org tasks (agenda/tasks)
  → seed history.jsonl (+ optional mappings) for report/topics/review
  → Rich save_svg for Wave A/B/C commands
  → existing TUI desk capture retained

docs/product/assets/captures/*.svg   committed, regenerable
docs/product/guides|concepts|…       embed shots + Mermaid
```

**Invariants**

- Captures regenerable with `uv run python scripts/docs-capture.py` (no live org).
- Fixture titles/ids fictional and stable (`acme` / demo names only).
- `mkdocs build --strict` green; pytest asserts required SVG paths.

**Sequencing**

1 → 2 (journey needs A/B shots). 3 can start after 1. 4 needs some JSON-capable shots
from 1. 5 adds Wave C + outbound prose; depends on 1, pairs with 3 diagrams.

## Breakdown / sub-specs

- [x] Time+ops demo fixture and Wave A/B SVG captures (project: Meta-Tools) — SPEC-0154
- [x] Journey rewrite: home, getting-started forks, daily/weekly guides (project: Meta-Tools) — SPEC-0155
- [x] Architecture and lifecycle pages (project: Meta-Tools) — SPEC-0156
- [x] Agent surface guide: schemas, skills map, JSON recipes (project: Meta-Tools) — SPEC-0157
- [x] Outbound/multi-project depth and Wave C captures (project: Meta-Tools) — SPEC-0158

Sequencing: child 1 first; child 2 after 1; children 3–5 after 1 (3∥4∥5 where possible).

## Acceptance criteria

- [x] Cold reader sees **time and ideas** in the first viewport (home/getting-started).
- [x] Daily and weekly operating guides exist and embed real Wave A/B SVGs.
- [x] Architecture/lifecycle page documents storage topology + DoD matrix.
- [x] Agent guide documents primary `--json` schemas and skill→CLI map.
- [x] Outbound guide teaches export → implement → pull-status/sweep → SHIPPED as required ops.
- [x] Capture script regenerates all required SVGs without live user data; tests + mkdocs strict green.

## Test plan

- **Integration:** `uv run python scripts/docs-capture.py`; `uv run pytest tests/test_docs_captures.py`; `mkdocs build --strict`.
- **Manual:** open home, getting-started, daily/weekly, architecture, agent, outbound pages; confirm SVGs and diagrams render.
- **Regression:** full `uv run pytest` green.

## Rollout / sequencing

Land child 1 immediately (stop underselling). Then journey rewrite. Close SPEC-0148 leftover
embeds via journey child or a one-line epic note. Architecture / agent / outbound can ship
as soon as their AC + embeds are ready.

## Definition of done

- [x] All child specs `done` or `superseded`.
- [x] Integration test plan executed; suite green.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

- None blocking accept — D2 and team playbook stay deferred per Non-goals.


## Shipped notes

Children SPEC-0154…0158 shipped: time fixture + Wave A/B/C SVGs, journey ops guides, architecture/lifecycle, agent surface, outbound close-the-loop docs.
