---
id: SPEC-0027
title: Prefix facet inheritance for colon-suffixed topics
status: done
owner: user
created: 2026-07-22
updated: 2026-07-22
milestone: "M4: cli ergonomics"
kind: feature
tags: [mapping, facets, topics, ergonomics]
source_idea: IDEA-013
depends_on: [SPEC-0008]
---

## Context

Promoted from idea `IDEA-013`.

Many base topics are `prefix:suffix`. Parents were mapped; children stayed unmapped under
exact-key `mappings.yaml`. v1 inherits facets from the prefix before the first `:`.

## Goals / Non-goals

**Goals**
- Exact mapping wins; else inherit from first-`:` parent key if mapped.
- Shared resolver for report `--by`, export columns, topics display / `--unmapped`.

**Non-goals**
- `prefix:*` globs; multi-colon walk; materializing inherited keys into YAML.

## Decision

`rules.resolve_facets(cfg, topic, mappings=None)` — exact, else parent before first `:`.
Wired through `_regroup`, export, and `topics`.

## Design

Shipped as designed. Call sites in `src/wt/report.py` use `resolve_facets`. `wt map` /
`load_mappings` / `set_facets` unchanged.

## Alternatives considered

As accepted: globs deferred; multi-level deferred; materialize rejected.

## Acceptance criteria

- [x] `resolve_facets` implements exact-then-first-colon-parent inheritance.
- [x] `wt report --by bucket` / export attribute `parent:child` hours to parent's bucket.
- [x] Exact child mapping overrides inheritance.
- [x] `wt topics` shows inherited facets; `--unmapped` excludes inherited-only topics.
- [x] `example-ats-1:foo` does not inherit from `example-ats`.
- [x] `tests/test_facet_inherit.py`; full suite green.
- [x] No change to `wt map` write path or mappings.yaml schema.

## Test plan

- **Automated:** `tests/test_facet_inherit.py`. ✓
- **Manual:** `wt topics` shows `example-ats:…` → `bucket=Example`; `--unmapped` dropped from ~51
  to ~34 (children of mapped parents cleared). ✓
- **Regression:** full `uv run pytest`. ✓

## Rollout / migration

Read-time only. Remap children only when they should not follow the parent.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

_None._
