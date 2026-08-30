---
id: SPEC-0120
title: "Per-project idea extension schema DSL required vs optional"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
kind: feature
parent: SPEC-0118
depends_on: [SPEC-0119]
milestone: "M6: idea extensions"
source_idea: IDEA-203
tags: [ideas, extensions, schema, config]
---

## Context

Child of [SPEC-0118](./0118-project-namespaced-idea-extensions-org-ext-schema.md)
(IDEA-203). Declare what Ext keys a project expects without interpreting their meaning.

## Goals / Non-goals

**Goals**
- Config SoT: top-level `idea_extensions:` map keyed by project name.
- Each project entry: `required: [KEY, …]`, `properties: { KEY: { type: string|enum,
  values?: […] } }`.
- Loader/normalize helpers for validators (SPEC-0121) and UI completers (SPEC-0122).
- No schema for a project ⇒ freeform Ext allowed.

**Non-goals**
- Full JSON Schema / `$ref`.
- Schemas stored on each idea.
- Enforcement/lint behavior (SPEC-0121) beyond providing the schema API.
- Embedding schema under `outbox_targets` (routing stays separate).

## Decision

```yaml
idea_extensions:
  Example:
    required: [DUT]
    properties:
      DUT: { type: string }
      NODE: { type: string }
      campaign_id: { type: string }
  PFW-Intelligence:
    required: []
    properties:
      campaign_id: { type: string }
```

- Keys in `required` must also appear under `properties` (lint config at load or first use).
- `enum` requires non-empty `values`.
- Unknown project names in `idea_extensions` warn like unknown associations (permissive) or
  hard-fail — prefer warn at config load, hard-fail only on write against that schema
  (SPEC-0121).

## Design

- `DEFAULT_CONFIG["idea_extensions"] = {}`.
- `extension_schema_for(cfg, project) -> dict|None`.
- Document in WORKFLOW one-liner; no skill required in this child.

## Alternatives considered

- **Schema under outbox_targets** — rejected; mixes routing with Ext DSL.
- **Required at capture** — rejected (epic).

## Acceptance criteria

- [x] Config loads `idea_extensions` and exposes per-project schema to library callers.
- [x] Invalid schema shape (required key missing from properties, empty enum) fails closed
      with a clear error when the schema is used.
- [x] Project with no entry remains freeform (None schema).
- [x] I can declare DUT required for Example without code changes in wt domain modules.

## Test plan

- **Automated:** config fixtures; schema helper unit tests.
- **Manual:** sample config.yaml snippet in WORKFLOW or spec example.
- **Regression:** default empty map — no behavior change.

## Clock Log

(use `wt idea clock-in/out` on IDEA-203)

## Rollout / migration

Additive config. Land after SPEC-0119.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; tests pass; manual noted.
- [x] No regressions; ledger updated; spec matches ship.

## Open questions

(none)
