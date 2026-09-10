---
id: SPEC-0059
title: "Static boilerplate TemplateScheme as a config-dir manifest"
status: done
owner: user
created: 2026-07-24
updated: 2026-09-09
source_idea: IDEA-017
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [specs, export, adapters, config]
depends_on: [SPEC-0058]
supersedes: [SPEC-0029]
---

## Context

Promoted from `IDEA-017`. Some outbound consumers need a richer task-spec shape: fixed
boilerplate interleaved with wt-sourced fields in the same section. SPEC-0058 shipped
`TemplateScheme` manifests loadable from `$WT_CONFIG_DIR/schemes/`. This spec adds
`static` sections with `{{field}}` / `{{field:checkbox}}` placeholders and ships a
generic in-repo example.

## Goals / Non-goals

**Goals**
- `TemplateScheme` supports `static` sections with placeholder substitution.
- Ship a generic example manifest (`docs/examples/schemes/static-boilerplate-example.toml`).
- Mark SPEC-0029 superseded (its code-plugin approach was never built).

**Non-goals**
- Built-in Python schemes for customer-specific shapes (withdrawn; see SPEC-0161).
- Auto-install into `$WT_CONFIG_DIR`.
- Vendoring real customer templates into this public tree.

## Decision

Extend `TemplateScheme` with optional `static` per section. Ship a fictional example only.

## Design

- `_substitute` in `template_scheme.py`.
- Example is not registered by wt; copy into `$WT_CONFIG_DIR/schemes/` to use.

## Acceptance criteria

- [x] `static` sections substitute placeholders.
- [x] Example manifest loads and is config-dir-installable.
- [x] SPEC-0029 superseded.

## Test plan

- Automated: `tests/test_export_schemes.py` (static rendering + example manifest).
- Regression: `uv run pytest`.

## Definition of done

- [x] AC met; tests pass; no customer-branded adapter ships in-tree (SPEC-0161).
