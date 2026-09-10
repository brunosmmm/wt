---
id: SPEC-0161
title: "Remove branded export adapter from the public tree"
status: done
owner: user
created: 2026-09-09
updated: 2026-09-09
milestone: "M3: idea→spec pipeline"
kind: feature
tags: [export, privacy, adapters]
supersedes: [SPEC-0029, SPEC-0034, SPEC-0037, SPEC-0047]
---

## Context

The public tree previously shipped a built-in export scheme and docs branded for one
customer's downstream task-runner product. That adapter and branding must not remain in
this repository. Org-specific shapes stay in the operator's config dir (SPEC-0058).

## Goals / Non-goals

**Goals**
- Remove the built-in branded Python export scheme from the package.
- Remove that product's name and bundle id from public docs, examples, CLI help, tests,
  and git history.
- Keep `wt-native`, `plain-md`, and a generic static-boilerplate TemplateScheme example.
- Mark the branded-adapter feature specs superseded by this withdrawal.

**Non-goals**
- Shipping a public drop-in replacement for the removed adapter.
- Changing SPEC-0058 config-dir loading.

## Decision

Delete the branded scheme module and its registration. Replace the branded example
manifest with a neutrally named generic TemplateScheme example. Scrub docs and rewrite
git history to purge the brand strings.

## Design

- Drop the scheme import from `export_schemes/__init__.py`.
- Neutralize CLI help/examples that named the brand.
- Delete scheme-specific tests; keep TemplateScheme static-section tests on the generic example.
- Specs 0029/0034/0037/0047/0059: `status: superseded`, `superseded_by: SPEC-0161`, short
  withdrawal note only.
- SPEC-0016: remove the branded product as the named exemplar.
- History rewrite + force-push.

## Alternatives considered

- **Rename in place** — rejected: still ships the customer workflow under an alias.
- **Private-only adapter package** — out of scope for this public purge.

## Acceptance criteria

- [x] `wt spec schemes` does not list the removed scheme.
- [x] No brand / former scheme-id strings remain under `docs/`, `src/`, `tests/`.
- [x] Generic TemplateScheme example remains; its tests pass.
- [x] Spec lint + ledger clean; history rewrite force-pushed.

## Test plan

- `uv run pytest tests/test_export_schemes.py`
- `python3 tools/spec_lint.py --write-ledger`
- `rg over docs/src/tests for the former scheme id / product name → empty

## Definition of done

- [x] AC met; tests green; history purged; `main` force-pushed.
