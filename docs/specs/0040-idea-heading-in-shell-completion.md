---
id: SPEC-0040
title: Show idea heading beside IDEA-id in shell completion
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
tags: [cli, ergonomics, completion]
depends_on: [SPEC-0039]
---

## Context

After SPEC-0039, `wt idea show <TAB>` lists bare `IDEA-034` ids. Fish (and zsh) can show a
description next to each value via Click `CompletionItem(help=…)`. Users want the idea
heading as that description.

## Goals / Non-goals

**Goals**
- `complete_idea_id` attaches a clipped heading as `help` on each `CompletionItem`.
- Fish TAB shows id + heading description.

**Non-goals**
- Descriptions for every other completer (specs/outbound/tasks can follow later).
- Changing which ideas are candidates (still open/non-done).

## Decision

Extend `_items` to accept an optional `helps` map; `complete_idea_id` passes
`{id: heading}`. Clip help to ~72 chars on a word boundary.

## Design

Shipped: `_clip_help`, `_items(..., helps=)`, `complete_idea_id` with headings; tests.

## Acceptance criteria

- [x] Idea id completions include non-empty `help` from the heading.
- [x] Help is single-line and length-capped.
- [x] Tests + pytest green; ledger/lint clean.

## Test plan

- **Automated:** `tests/test_completion.py`. ✓
- **Manual:** fish `wt idea show <TAB>` shows headings.
- **Regression:** full pytest.

## Rollout / migration

No install required (live completer).

## Definition of done

- [x] AC met; tests green; spec/ledger current.

## Open questions

_None._
