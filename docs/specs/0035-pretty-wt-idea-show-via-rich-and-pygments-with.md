---
id: SPEC-0035
title: Pretty wt idea show via Rich and Pygments with --plain escape
status: done
owner: user
created: 2026-07-23
updated: 2026-07-23
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, ideas, ergonomics, rich]
source_idea: IDEA-043
depends_on: [SPEC-0026, SPEC-0030]
---

## Context

Promoted from `IDEA-043`. `wt idea show` printed a plain string from
`explore.format_idea_show` via `click.echo`: literal org section stars (`** Summary`,
`***` Log stamps), no emphasis rendering. Enrichment bodies are org-native (SPEC-0030).
The rest of the CLI already uses Rich (`console.py`).

## Goals / Non-goals

**Goals**
- Human `wt idea show` pretty-prints with **Rich + Pygments** org lexer, theme
  **`manni`**.
- **`--plain`** forces plain text; **`--json`** unchanged; non-TTY defaults to plain.

**Non-goals**
- Multi-level header → bullet glyph substitution.
- Full org TUI / fold / images.

## Decision

TTY + not `--plain`/`--json` → `console.print(Syntax(text, "org", theme="manni",
word_wrap=True))`. Otherwise plain `format_idea_show` on stdout.

## Design

Shipped:
- `explore.idea_show_use_pretty` / `explore.print_idea_show`
- `cli.idea_show_cmd --plain`
- `docs/WORKFLOW.md` one-liner
- `tests/test_idea_show_pretty.py`

## Alternatives considered

- org→Markdown→Rich Markdown — rejected; Rich+Pygments locked.
- Always pretty — rejected; `--plain` and pipes.

## Acceptance criteria

- [x] TTY show uses Rich + Pygments org lexer.
- [x] `--plain` is plain (no Syntax ANSI).
- [x] `--json` unchanged.
- [x] Non-TTY defaults to plain.
- [x] No header→bullet substitution.
- [x] Tests + full pytest green.

## Test plan

- **Automated:** `tests/test_idea_show_pretty.py` (gates, plain match, ANSI on
  `Console(force_terminal=True)`, CLI `--plain`/`--json`/help).
- **Manual:** `wt idea show IDEA-043 --plain` plain; without `--plain` on a real TTY
  highlights (non-TTY / captured shells stay plain by design).
- **Regression:** `uv run pytest` (289 passed).

## Rollout / migration

No data migration.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; pytest green; manual noted.
- [x] Spec matches shipped.
- [x] Ledger regenerated; `spec_lint` exits 0.

## Open questions

_None._
