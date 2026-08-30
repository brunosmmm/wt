---
id: SPEC-0121
title: "Idea Ext write-time enforcement and lint --strict"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
kind: feature
parent: SPEC-0118
depends_on: [SPEC-0119, SPEC-0120]
milestone: "M6: idea extensions"
source_idea: IDEA-204
tags: [ideas, extensions, lint]
---

## Context

Child of [SPEC-0118](./0118-project-namespaced-idea-extensions-org-ext-schema.md)
(IDEA-204). Mirror workstreams: hard-fail bad writes when schema exists; lint for
hand-edit drift.

## Goals / Non-goals

**Goals**
- On Ext write (set/clear) when schema exists: reject unknown keys; reject clearing a
  required key; after write, required keys must all be present.
- `wt idea ext lint` [selector | `--all`]: report missing required / unknown keys /
  Ext without `:PROJECT:` mismatch as designed.
- `--strict`: exit non-zero if any finding.
- No schema ⇒ no write-time Ext validation (namespace rules from SPEC-0119 still apply).

**Non-goals**
- Requiring Ext at bare capture.
- Promote/export gate (deferred optional epic item).
- Auto-inserting empty required keys.

## Decision

Enforcement points:

| Event | Behavior |
|-------|----------|
| `set_idea_extension` / clear | Schema validate; ValueError on violation |
| `wt idea ext lint` | Report-only list of problems |
| `… lint --strict` | Same + exit 1 if any problem |
| Bare `wt idea` capture | Never requires Ext |

Stale unknown keys on disk still **read** in show/JSON; lint is how operators notice.

## Design

- `validate_extension_map(cfg, project, mapping, *, updating=False) -> list[str]` problems.
- Wire into SPEC-0119 writers.
- CLI lint command may ship in this child or SPEC-0122 — library here is mandatory; CLI
  entry at least `wt idea ext lint` before epic done (prefer this child or 0122, not both
  duplicated).

## Alternatives considered

- **Warn-only writes** — rejected; schema would be toothless.
- **Promote gate in v1** — deferred.

## Acceptance criteria

- [x] Illegal Ext write raises; legal write succeeds.
- [x] Lint lists missing required / unknown keys; `--strict` fails closed.
- [x] Ideas without schema still accept freeform Ext writes.
- [x] I can catch Emacs hand-edit drift with lint without mutating files.

## Test plan

- **Automated:** schema fixtures; write failures; lint strict exit codes.
- **Manual:** hand-edit Ext → lint reports; fix → clean.
- **Regression:** ideas without Ext unaffected.

## Clock Log

(use `wt idea clock-in/out` on IDEA-204)

## Rollout / migration

After 0119+0120. Existing freeform Ext on schemaless projects unchanged.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; tests pass; manual noted.
- [x] No regressions; ledger updated; spec matches ship.

## Open questions

(none)
