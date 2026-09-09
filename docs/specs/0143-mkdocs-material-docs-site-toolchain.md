---
id: SPEC-0143
title: "MkDocs Material docs site toolchain"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M8: product documentation"
kind: feature
parent: SPEC-0141
tags: [docs]
depends_on: [SPEC-0142]
source_idea: IDEA-356
---

## Context

Child of [SPEC-0141](./0141-human-product-documentation-site-showcase.md). [SPEC-0142](./0142-docs-product-ia-narrative-and-glossary.md)
landed the Markdown tree under `docs/product/`. This spec wires **MkDocs Material** so
that tree builds and serves as a navigable site.

Promoted from `IDEA-356`.

## Goals / Non-goals

**Goals**

- `mkdocs.yml` with Material theme, search, and nav matching `docs/product/`.
- `docs_dir: docs/product` so `docs/specs/` stays out of the default site.
- Optional `docs` extra (`mkdocs-material`) plus a serve script.
- Automated proof: `mkdocs build --strict` succeeds (via pytest when the extra is
  installed, and via `dev` dependency group so CI has it).

**Non-goals**

- GitHub Pages / Cloudflare deploy (optional later; local `site/` artifact is enough).
- Filling guide/capability prose (SPEC children for IDEA-357/358).
- Slimming the root README (IDEA-360).

## Decision

Use **MkDocs Material** with `docs_dir: docs/product`. Declare `mkdocs-material` under
`[project.optional-dependencies].docs` and also pin it in `[dependency-groups].dev` so
`uv sync` / CI can run a strict build without a separate install path. Ship
`scripts/docs-serve.sh` → `uv run mkdocs serve`. Product Markdown that pointed at
repo-root files outside `docs_dir` uses plain paths (not relative Markdown links) so
`--strict` does not fail on missing pages.

## Design

- Root `mkdocs.yml`: site_name, theme material, plugins search, nav for Home / Guides /
  Concepts / Capabilities / Reference / Contribute.
- Build output: `site/` (gitignored).
- Test: `tests/test_docs_mkdocs_build.py` runs `mkdocs build --strict` into a temp
  directory (or default `site/` under cwd) and asserts exit 0.

## Alternatives considered

- **docs_dir: docs/** — would pull specs into the tree unless carefully excluded; lost to
  keep archaeology out of the default nav.
- **Sphinx / Docusaurus** — heavier; Material is Python-native and matches the epic.

## Acceptance criteria

- [x] `mkdocs.yml` exists at repo root with Material theme and nav covering product IA.
- [x] `uv run mkdocs build --strict` succeeds with `docs`/`dev` deps installed.
- [x] `scripts/docs-serve.sh` starts serve via uv/mkdocs.
- [x] `docs` optional extra declares `mkdocs-material`.
- [x] Pytest covers the strict build.
- [x] Product pages do not use Markdown links that escape `docs_dir` (strict-safe).

## Test plan

- **Automated:** `tests/test_docs_mkdocs_build.py` — invoke `mkdocs build --strict`;
  assert returncode 0. Also assert `mkdocs.yml` and `scripts/docs-serve.sh` exist.
- **Manual:** `scripts/docs-serve.sh` → open home; confirm nav + search.
- **Regression:** existing `tests/test_docs_product_ia.py` and full `uv run pytest` stay green.

## Clock Log

Prefer `wt idea clock-in` / `clock-out` on IDEA-356.

## Rollout / migration

1. Accept this spec.
2. Add deps + `mkdocs.yml` + serve script + fix out-of-tree links.
3. Run strict build + pytest; mark done; reconcile IDEA-356.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_(none — layout choice locked: `docs_dir: docs/product`.)_
