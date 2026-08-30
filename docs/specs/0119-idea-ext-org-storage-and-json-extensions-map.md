---
id: SPEC-0119
title: "Idea Ext org storage and JSON extensions map"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
kind: feature
parent: SPEC-0118
milestone: "M6: idea extensions"
source_idea: IDEA-202
tags: [ideas, org, extensions]
---

## Context

Child of [SPEC-0118](./0118-project-namespaced-idea-extensions-org-ext-schema.md)
(IDEA-202). First slice: persist and read project-private key/value maps on the idea subtree.

## Goals / Non-goals

**Goals**
- Store Ext as `** Ext <Project>` + nested `:PROPERTIES:` (string values).
- Library: get all extensions / get one project map / set key / clear key / ensure headline.
- `wt.idea.v1` additive field `extensions` when non-empty.
- L2 Ext headlines remain enrichment (never tasks/agenda).

**Non-goals**
- Schema validation (SPEC-0120/0121).
- CLI/desk (SPEC-0122).
- L1 `:EXT_PROJECT_KEY:` prefixed properties in v1.

## Decision

Canonical shape:

```org
* INCUBATE …
  :PROPERTIES:
  :ID: IDEA-NNN
  :PROJECT: Example
  :END:
  ** Ext Example
     :PROPERTIES:
     :DUT: pc4
     :NODE: n1
     :END:
```

`<Project>` matches the project name string used in `:PROJECT:` / `wt projects`. Multiple
`** Ext …` siblings allowed only if explicitly writing another namespace (v1 may restrict to
the idea's `:PROJECT:` only — prefer single Ext matching `:PROJECT:` unless Design at ship
documents multi).

## Design

- Reader walks idea span for `** Ext <name>` + drawer → `dict[str, dict[str, str]]`.
- Writer creates/updates drawer via line-oriented atomic write (same family as
  `_inject_property`, but on the Ext headline).
- `idea_show_payload` / list rows: include `extensions` when non-empty (list rows optional —
  show payload required).
- Do not extend `_STAR_SECTION_RE` Summary/Log prose replace for Ext — dedicated API.

## Alternatives considered

- **Prefixed L1 properties** — rejected for v1 (epic).
- **Sidecar files** — rejected (human).

## Acceptance criteria

- [x] Round-trip set/get/clear Ext keys on an idea in org.
- [x] `wt idea show ID --json` includes `extensions` when set.
- [x] Ext headlines do not appear in `wt tasks` / agenda.
- [x] I can store Example-like keys without changing core property vocabulary.

## Test plan

- **Automated:** temp ideas.org fixtures; enrichment filter; JSON payload.
- **Manual:** Emacs shows Ext drawer under idea.
- **Regression:** existing explore/property tests.

## Clock Log

(use `wt idea clock-in/out` on IDEA-202)

## Rollout / migration

No migration of existing ideas. Land before schema/UI.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; tests pass; manual noted.
- [x] No regressions; ledger updated; spec matches ship.

## Open questions

(none)
