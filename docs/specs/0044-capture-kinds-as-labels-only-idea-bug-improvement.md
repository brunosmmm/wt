---
id: SPEC-0044
title: "Capture kinds as labels (idea/bug/improvement/chore)"
status: done
owner: user
created: 2026-07-24
updated: 2026-07-24
milestone: "M4: cli ergonomics"
kind: feature
tags: [ideas, capture, ergonomics]
source_idea: IDEA-054
depends_on: [SPEC-0012, SPEC-0018, SPEC-0023, SPEC-0026]
---

## Context

Promoted from `IDEA-054`. The open-idea list mixes vague R&D with clear defects and polish
items, but every capture shares the same IDEA/INCUBATE vocabulary. Diversifying *states*
(parallel BUG/IMPROVEMENT TODO machines) was rejected; we only need a triage **label**.

Today `add_idea` → `add_task` can set `:ID:` / `:PROJECT:` / `:EPIC:` / `:TOPIC:` and freeform
headline tags. There is no first-class capture kind. Spec frontmatter `kind`
(`feature`|`epic`|…) is a different namespace — do not conflate.

## Goals / Non-goals

**Goals**
- Closed idea kinds: `idea` | `bug` | `improvement` | `chore` (default `idea` when omitted).
- Persist as org `:KIND:` on the idea drawer (same pattern as `:PROJECT:`).
- Capture / mutate / list / show / JSON expose kind; `wt ideas --kind` filters.
- Document that kinds are labels only — idea→explore→spec pipeline and `next_step_for_idea`
  stay unchanged in v1.

**Non-goals**
- New `#+TODO` keywords or parallel state machines.
- Encoding kind as tags only (`:bug:` etc.).
- Changing promote gates, Summary requirements, or `wt next` command strings by kind.
- Auto-routing bugs to `wt add` / org tasks (may be a later idea).
- Renaming or overlapping with spec frontmatter `kind`.

## Decision

Add a first-class **`:KIND:`** property on ideas with a closed enum, defaulting to `idea`.
Surface it on capture (`--kind`), mutation (`wt idea kind`), listing/filter, and show/JSON.
Keep workflow next-hints identical regardless of kind; skills may *advise* shorter ceremony
for clear `bug`/`chore` captures, but tooling does not enforce alternate paths.

## Design

### Enum and storage

- Allowed values (lowercase): `idea`, `bug`, `improvement`, `chore`
  (`org_write.IDEA_KINDS`).
- Written as `:KIND: <value>` in the idea `:PROPERTIES:` drawer.
- Capture with `--kind` / `kind=` always writes the property; omit at capture → no `:KIND:`;
  read via `idea_kind(task)` resolves missing/unknown to `idea`.
- Invalid values → `ValueError` / Click error.

### Write path

- `add_task` / `add_idea(..., kind=None)`; `set_idea_kind(cfg, selector, kind)`.
- CLI: `wt idea … --kind`; `wt idea kind <id> --set`; `IdeaGroup` whitelists `--kind`.

### Read / display

- `idea_row` / `idea_show_payload` always include `"kind"`.
- Plain show: `kind:` line; Rich `wt ideas` / `wt next`: `kind` column.
- `wt ideas --kind bug` filters on resolved kind.

### Next / skills

- `workflow.next_step_for_idea`: no branch on kind.
- `docs/WORKFLOW.md` + `skills/wt-capture` document `--kind` as advisory triage label.

## Alternatives considered

- **Tag-only (`:bug:`)** — lost: freeform tags collide; harder to validate/filter uniformly.
- **New TODO keywords** — lost: user lock; overloads org state for triage metadata.
- **v1 next-hint changes by kind** — deferred: label-first; revisit if triage still noisy.
- **Open string kinds** — lost: closed set keeps lists and Completions sane.

## Acceptance criteria

- [x] `wt idea "…" --kind bug` writes `:KIND: bug` (and assigns IDEA-NNN as today).
- [x] Omitting `--kind` leaves no `:KIND:` (or equivalent) and reads as `idea`.
- [x] Invalid `--kind` fails the command.
- [x] `wt idea kind <id> --set improvement` updates `:KIND:`.
- [x] `wt idea show` / `--json` and `wt ideas --json` expose resolved `kind`.
- [x] `wt ideas --kind bug` lists only matching ideas (resolved default applies).
- [x] `next_step_for_idea` behavior unchanged for same Summary/SPEC state regardless of kind.
- [x] Tests cover capture, mutate, filter, show/json; WORKFLOW (or skill) mentions `--kind`.

## Test plan

- **Automated:** `tests/test_idea_kind.py` — capture with/without kind; invalid; `kind --set`;
  row/show; `--kind` filter; next-step equality before/after. Full suite 332 passed.
- **Manual:** captured `--kind bug`, show/filter, `kind --set chore`, then DROPPED smoke idea.
- **Regression:** pre-existing idea/json tests green.

## Rollout / migration

No backfill required — missing `:KIND:` means `idea`. Optionally label known defects via
`wt idea kind … --set bug`.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; automated tests pass (`uv run pytest`); manual steps performed.
- [x] No regressions.
- [x] Spec body updated to match what shipped.
- [x] `docs/LEDGER.md` updated (status + date).

## Open questions

_None._
