---
id: SPEC-0036
title: Configurable Pygments theme for wt idea show
status: done
owner: user
created: 2026-07-23
updated: 2026-07-23
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, ideas, ergonomics, rich, config]
depends_on: [SPEC-0035]
---

## Context

SPEC-0035 shipped `wt idea show` with Rich + Pygments org highlighting. Theme taste is
personal; users need a config knob. An early default of `manni` (light theme: near-black
text) was unreadable / bizarre on dark terminals — the common case for this CLI.

## Goals / Non-goals

**Goals**
- `config.yaml` key `idea_show_theme` selects the Pygments style (default `nord`).
- Missing/blank values fall back to `nord`.
- Pretty show uses the terminal background (no painted theme panel).

**Non-goals**
- Per-command `--theme` flag (config is enough).
- Theme picker / listing command.
- Changing non-TTY / `--plain` / `--json` gates.

## Decision

`explore.idea_show_theme(cfg)` → strip; empty/missing → `nord`. Pass to
`Syntax(..., theme=..., background_color="default")`. Document in README.

## Design

Shipped:
- `DEFAULT_CONFIG["idea_show_theme"] = "nord"`
- `explore.idea_show_theme` / `print_idea_show` (`background_color="default"`)
- README + WORKFLOW
- `tests/test_idea_show_pretty.py`

## Alternatives considered

- **Default `manni`** — rejected after dark-terminal check (black body text).
- **CLI `--theme` only** — rejected; durable preference belongs in config.
- **Paint theme background** — rejected; looks like a misplaced code panel.

## Acceptance criteria

- [x] Default theme is `nord` when key absent.
- [x] `idea_show_theme` in cfg is passed to Rich `Syntax`.
- [x] Blank/whitespace theme falls back to `nord`.
- [x] Pretty path uses `background_color="default"`.
- [x] `--plain` / non-TTY / `--json` unchanged.
- [x] Tests + pytest green; ledger/lint clean.

## Test plan

- **Automated:** `tests/test_idea_show_pretty.py` (default + override + blank + bg). ✓
- **Manual:** TTY `wt idea show` readable on dark terminal; override via config.
- **Regression:** `uv run pytest`.

## Rollout / migration

No data migration. If a user already set `idea_show_theme: manni`, that still wins.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; pytest green.
- [x] Spec matches shipped; ledger regenerated; `spec_lint` exits 0.

## Open questions

_None._
