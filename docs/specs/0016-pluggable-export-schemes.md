---
id: SPEC-0016
title: Pluggable export schemes
status: done
owner: user
created: 2026-07-16
updated: 2026-09-09
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [specs, export, adapters]
parent: SPEC-0011
depends_on: [SPEC-0015]
---

## Context

[SPEC-0015](./0015-outbound-spec-export.md) exports outbound specs by file-drop in wt's own
(`wt-native`) shape. Different downstream consumers ingest different shapes, so export needs
a **pluggable scheme layer**: select a renderer, validate required fields, write artifacts
into the target tree without clobbering foreign files.

## Goals / Non-goals

**Goals**
- An `ExportScheme` registry the SPEC-0015 exporter delegates to; `wt-native` is the default.
- Scheme selection via `wt spec export --scheme <name>` and optional per-target defaults;
  `wt spec schemes` lists available schemes.
- Two authxxing tiers: **declarative** manifests (TemplateScheme) and **code** plugins.
- Built-ins that ship in this public tree stay product-agnostic (`wt-native`, `plain-md`,
  plus config-dir TemplateScheme examples).

**Non-goals**
- Completing every field a foreign consumer might want (emit faithful seeds / fill markers).
- Emitting architecture / codebase / style-guide baselines derived from the target repo.
- Live orchestration with any external runner (still file-drop).
- Shipping customer-branded adapters in this public repository (see SPEC-0161).

## Decision

Introduce `ExportScheme` + registry. `wt spec export` resolves scheme
(CLI > target config > `wt-native`), validates, and writes `OutputFile`s using owned /
splice / native-spec modes from SPEC-0015.

## Design

### Emit scope & non-clobber

- Schemes declare which artifacts they own (`--emit` can narrow a run).
- Shared files (e.g. a project plan) use **splice** by id; divergent content needs `--force`.
- Provenance (SPEC-0015) records what wt wrote.

### Interface & registry (`src/wt/export_schemes/`)

- `ExportScheme`: `name`, `description`, `required_fields`, `artifacts`, `validate`, `render`.
- Built-ins register on package import; user TemplateScheme manifests load from
  `$WT_CONFIG_DIR/schemes/` (SPEC-0058/0059).

### Built-ins (public tree)

- `wt-native` — portable copy + consumption contract (SPEC-0015).
- `plain-md` — minimal flat remap via TemplateScheme manifest.
- Additional org-specific shapes: config-dir only (not vendored here).

## Alternatives considered

- **Hard-code one foreign shape in core** — rejected: couples wt to a single consumer.
- **Declarative-only** — rejected for cases needing allocation/decomposition logic; keep
  code plugins available, but do not ship customer-branded ones in public wt.

## Acceptance criteria

- [x] Registry exists; `wt-native` is default; `wt spec schemes` lists schemes.
- [x] `--scheme` selects a registered renderer.
- [x] Non-clobber / splice semantics hold for owned and shared artifacts.
- [x] Public tree does not ship a customer-branded code adapter (SPEC-0161).

## Test plan

- Automated: `tests/test_export_schemes.py` (registry, wt-native, TemplateScheme).
- Regression: `uv run pytest`.

## Definition of done

- [x] AC met; tests pass; ledger current; branded adapter withdrawn (SPEC-0161).
