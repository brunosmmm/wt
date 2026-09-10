---
id: SPEC-0157
title: "Agent surface guide: schemas, skills map, JSON recipes"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0153
tags: [docs]
depends_on: [SPEC-0153]
source_idea: IDEA-395
---

## Context

Child of SPEC-0153. Agent builders get skills + scattered `--json` mentions but no schema
catalog or skill→CLI map in the product site.

## Goals / Non-goals

**Goals**

- Product guide listing primary `wt.*.v1` JSON schemas with example payloads.
- Skill → CLI command map for shipped agent skills.
- Copy-paste recipes for common automation loops.

**Non-goals**

- Changing JSON schema versions.
- Implementing new agent APIs.

## Decision

One guide under `docs/product/guides/` (or capabilities/agents) that is the agent front
door; link from getting-started agent fork (0155).

## Design

- Inventory schemas from live `--json` outputs / code (`schema` fields).
- Table: skill name → primary CLI verbs.
- Recipes: triage via hub/next; enrich idea; promote; generate/export (pointers to 0158).

## Acceptance criteria

- [x] Guide exists and is in MkDocs nav.
- [x] Documents ≥5 real schema ids with example shape.
- [x] Skill→CLI map covers the skills shipped by `wt skills`.
- [x] `mkdocs build --strict` passes.

## Test plan

- **Automated:** needles for schema ids + skills guide path.
- **Manual:** spot-check one recipe against CLI.
- **Regression:** skills capability page still links correctly.

## Definition of done

- [x] AC met; test plan executed; ledger updated; IDEA-395 reconciled.

## Open questions

- None.


## Shipped notes

Added `guides/agent-surface.md` (skill→CLI map, ≥9 schema ids, recipes); linked from getting-started Path C, guides index, skills capability; mkdocs strict + docs tests green.
