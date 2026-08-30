---
id: SPEC-0039
title: Idea-selector shell completion + compliance test for required completers
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, ergonomics, completion]
depends_on: [SPEC-0022]
---

## Context

Fish completion for `wt` is a **live** Click wrapper (`wt completion install` once). New
subcommands appear automatically. What does **not** appear automatically is dynamic value
completion: `wt idea show <TAB>` was empty because `@click.argument("selector")` lacked
`shell_complete=C.complete_idea_id`. Same gap on `log` / `summary` / `questions` / `retitle` /
`normalize-logs`. There was no checklist or test forcing completers when CLI surface grows.

## Goals / Non-goals

**Goals**
- Wire `complete_idea_id` on all idea `selector` arguments.
- Document the moving-forward rule: subcommands are free; **closed-set params need
  `shell_complete`**; fish install is rarely re-needed.
- Compliance test: walk the Click tree; every parameter whose name is in a required set must
  have a non-None `shell_complete` (unless Path/Choice already covers it).

**Non-goals**
- Completing free-text args (`text`, `title`, `note`, dates as free strings).
- Re-installing fish on every CLI change (script is dynamic).
- Expanding `known_epics` to outbound (separate).

## Decision

Fix the idea selectors now. Maintain `REQUIRED_SHELL_COMPLETE_NAMES` in `completion.py` and a
pytest that fails if any matching CLI param lacks a completer. Document the checklist in
README (Shell completion) and `docs/WORKFLOW.md`.

## Design

Shipped:
- `shell_complete=C.complete_idea_id` on idea `log|explore|normalize-logs|summary|questions|
  retitle|show` selectors
- `REQUIRED_SHELL_COMPLETE_NAMES`, `iter_cli_params`, `missing_required_shell_completes`
- `tests/test_completion.py` compliance + idea-show smoke
- README + WORKFLOW guidance

## Alternatives considered

- **Hand-maintained fish script of every subcommand** — rejected; SPEC-0022 already chose live
  Click generation.
- **Allowlist of exempt commands only** — rejected; name-based required set is clearer for
  authxxs (“any `selector` must complete”).

## Acceptance criteria

- [x] `wt idea show <TAB>` / bash_complete with `COMP_WORDS="wt idea show "` yields `IDEA-*`.
- [x] All idea `selector` args have `complete_idea_id`.
- [x] Compliance test fails if a required-name param lacks a completer.
- [x] README + WORKFLOW document the rule.
- [x] pytest green; ledger/lint clean.

## Test plan

- **Automated:** `tests/test_completion.py` — idea-show completion smoke + tree compliance. ✓
- **Manual:** fish `wt idea show <TAB>` after current `wt` on PATH.
- **Regression:** existing completion tests + full pytest.

## Rollout / migration

No data migration. Optional: `wt completion install --shell fish` if installed `wt` entrypoint
is stale.

## Definition of done

- [x] Acceptance criteria met; test plan executed.
- [x] Spec matches shipped; ledger regenerated; `spec_lint` exits 0.

## Open questions

_None._
