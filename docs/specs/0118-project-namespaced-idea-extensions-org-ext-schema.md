---
id: SPEC-0118
title: "Project-namespaced idea extensions (org Ext + schema + UI)"
status: done
owner: user
created: 2026-08-04
updated: 2026-08-04
kind: epic
milestone: "M6: idea extensions"
source_idea: IDEA-201
tags: [ideas, org, extensions, schema]
---

## Context

Promoted from `IDEA-201` after explore locked storage shape, schema/enforcement, and UI
needs. Ideas today share a flat core `:PROPERTIES:` vocabulary. Projects need **private**
structured fields (Example DUT/node, PFW `campaign_id`, …) without teaching wt a union schema
or using sidecar files. Those fields often hold project-internal state the core wt workflow
never drives — still must be deliberately readable/writable.

Example/PFW appear only as **example namespaces**; Meta-Tools owns the mechanism (single-root).

## Goals / Non-goals

**Goals**
- Org-native namespaced Ext on the idea subtree.
- Per-project schema (required vs optional + simple types) in config.
- Write-time enforcement + lint (`--strict`).
- CLI + desk + JSON UI over the same library mutators.
- Core remains opaque to domain values.

**Non-goals**
- Sidecar meta files beside ideas.org.
- Embedding campaign ledgers into ideas.
- Hub/table columns for arbitrary Ext keys.
- Domain widgets (DUT pickers) inside wt core.
- L1 prefixed `:EXT_EXAMPLE_*: ` dual path in v1.
- Promote/export hard gate in v1 (optional later child).

## Decision

Ship an epic whose contract is:

1. **Storage:** `** Ext <Project>` + nested `:PROPERTIES:` (opaque keys); JSON
   `extensions` on `wt.idea.v1`.
2. **Schema:** top-level config `idea_extensions:` keyed by project name.
3. **Enforce:** hard-fail illegal writes when schema exists; `wt idea ext lint` + `--strict`.
4. **UI:** `wt idea ext` CLI + desk metadata path; every write expressible on CLI; agents use
   CLI or library.

## Architecture / cross-cutting design

```
config idea_extensions[Project]  -->  validate on write / lint
org: ** Ext <Project> :PROPERTIES:  -->  library get/set  -->  CLI / desk / JSON
```

**Invariants**
- One mutator path (library); CLI/desk thin.
- Nested Ext children are enrichment (`_is_enrichment`) — never tasks.
- No schema for a project ⇒ freeform Ext still allowed under that project's Ext headline.
- Required keys do **not** apply at bare `wt idea` capture.
- Reserved core L1 property names never appear as Ext keys on the main drawer (Ext lives on
  the child headline anyway).

## Breakdown / sub-specs

- [x] [SPEC-0119](./0119-idea-ext-org-storage-and-json-extensions-map.md) — Ext org storage +
      JSON extensions map (IDEA-202)
- [x] [SPEC-0120](./0120-per-project-idea-extension-schema-dsl-required-vs.md) — Per-project
      schema DSL required vs optional (IDEA-203; depends_on 0119)
- [x] [SPEC-0121](./0121-idea-ext-write-time-enforcement-and-lint-strict.md) — Write-time
      enforcement + lint `--strict` (IDEA-204; depends_on 0119/0120)
- [x] [SPEC-0122](./0122-idea-ext-user-interface-to-get-set-project.md) — UI get/set Ext
      (IDEA-205; depends_on 0119; guided UX wants 0120/0121)

Sequencing: **202 → 203 → 204**; **205** after 202 (CLI usable); desk guided editing wants
203/204.

## Acceptance criteria

- [x] Ideas can store and round-trip project Ext via org + `wt.idea.v1` `extensions`.
- [x] Config schema can mark required/optional keys; writes and lint honor it.
- [x] Operators/agents can get/set Ext without hand-editing org (CLI at minimum).
- [x] Core wt workflow unchanged for ideas without Ext / without schema.
- [x] All child specs `done` or `superseded`.

## Test plan

- **Integration:** create idea with Ext; schema violate → write fails; lint `--strict`;
  CLI set/show; JSON shows `extensions`; full pytest green without requiring Ext on all ideas.
- **Manual:** Emacs-visible `** Ext …` drawer; desk edit if shipped in 205.
- **Regression:** existing property/explore/capture tests.

## Rollout / sequencing

Accept epic + children first; implement 202→203→204→205. Partial: storage alone is useful
with freeform Ext before schema lands.

## Definition of done

- [x] All child specs `done` or `superseded`.
- [x] Integration test plan executed; `uv run pytest` green.
- [x] Acceptance criteria met; epic body reflects what shipped.
- [x] `docs/LEDGER.md` regenerated.

## Open questions

(none — resolved on IDEA-201 before accept)
