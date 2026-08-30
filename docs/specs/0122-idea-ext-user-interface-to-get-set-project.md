---
id: SPEC-0122
title: "Idea Ext user interface to get/set project sidecar fields"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
kind: feature
parent: SPEC-0118
depends_on: [SPEC-0119]
milestone: "M6: idea extensions"
source_idea: IDEA-205
tags: [ideas, extensions, cli, tui]
---

## Context

Child of [SPEC-0118](./0118-project-namespaced-idea-extensions-org-ext-schema.md)
(IDEA-205). Projects track Ext state wt's core workflow does not own; operators/agents need
a deliberate UI so Ext is not Emacs-only.

## Goals / Non-goals

**Goals**
- CLI `wt idea ext` for show / set / clear / list (and lint entry if not already in 0121).
- Every Ext mutation expressible on the CLI (agents may also call the library).
- Desk metadata path to edit Ext for the idea's project (schema-guided when SPEC-0120
  present; enum → Choice).
- Rely on SPEC-0119 `extensions` in show/JSON for agent readback.

**Non-goals**
- Domain-specific pickers in wt core (Example DUT UI stays in project skills calling CLI).
- Hub columns for Ext keys.

## Decision

- **CLI first** (required for this child to be `done`).
- **Desk** in the same child but may land immediately after CLI; must use the same mutators.
- Schema enums → Click/`Choice` / desk chooser; other types free-text with lint from 0121.
- Soft-depend on 0120/0121 for guided UX; CLI set/get works freeform once 0119 exists.

## Design

- Click group under `idea`: `ext show|set|clear|list|lint` — exact flags in `--help` only.
- Desk: extend metadata flow; list keys from schema properties ∪ existing drawer.
- Completers for project Ext keys when schema exists (`completion.py`).

## Alternatives considered

- **Desk-only** — rejected; agents/scripts need CLI.
- **Library-only for agents** — rejected; every write must be CLI-expressible.

## Acceptance criteria

- [x] `wt idea ext set/show/clear` round-trips Ext for an idea.
- [x] Desk can edit Ext without hand-editing org (once desk slice lands).
- [x] Enum schema fields offer choices on CLI (when 0120 present).
- [x] I can update project-private state that wt workflow never reads as a first-class command.
- [x] No domain-specific widgets required in core.

## Test plan

- **Automated:** CliRunner ext set/show/clear; optional desk pilot if patterns exist.
- **Manual:** CLI + desk against a Example-schema fixture project name.
- **Regression:** ideas without Ext; `wt idea --help` lists ext.

## Clock Log

(use `wt idea clock-in/out` on IDEA-205)

## Rollout / migration

After SPEC-0119. Desk may follow CLI in the same PR series. Wire lint CLI to 0121 library.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; tests pass; manual noted.
- [x] No regressions; ledger updated; spec matches ship.

## Open questions

(none)
