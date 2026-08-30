---
id: SPEC-0091
title: "Capture routing: idea vs wt add (SPEC-0044 deferred)"
status: done
owner: user
created: 2026-07-28
updated: 2026-07-28
kind: feature
milestone: "M4: cli ergonomics"
source_idea: IDEA-107
parent: SPEC-0087
tags: [ideas, capture, routing, cli]
---

## Context

Child of [SPEC-0087](./0087-workstreams-and-concern-separation-routing.md). Closes the
auto-routing non-goal deferred by [SPEC-0044](./0044-capture-kinds-as-labels-only-idea-bug-improvement.md).
Human disposition (IDEA-107): soft CLI warn on `--kind bug` (not hard redirect); bug-only;
`--force-idea` escape; capture-time only; skills/WORKFLOW reinforce the fork.

## Goals / Non-goals

**Goals**
- Soft gate: `wt idea … --kind bug` warns and prints an equivalent `wt add …` line, then still
  writes the idea unless suppressed.
- `--force-idea` silences the warn (design-needed defects that truly belong in the idea pipeline).
- Skills + WORKFLOW state: actionable/bug-shaped → prefer `wt add`; `--kind bug` on ideas is
  for triage of *design* bugs that need explore→spec.

**Non-goals**
- Hard auto-route bug→task; NLP/actionability inference.
- Warn on improvement/chore; idea↔task repair/migration commands.
- Changing `:KIND:` semantics or removing `--kind bug` from ideas.

## Decision

- Trigger: idea capture path only, when normalized kind is `bug` and `--force-idea` is absent.
- Behavior: Rich yellow warn on stderr/console; still call `add_idea` (soft, not enforce-block).
- Suggested line: `wt add <text>` plus echoed association flags present on the capture
  (`--project`/`--tag`/`--priority`/`--key`/`--epic`/`--workstream`); omit `--kind` (tasks have
  no kind).
- Docs: update `wt-capture` skill + `docs/WORKFLOW.md` capture section.

## Design

- `cli.idea_capture_cmd`: `--force-idea` flag; after kind normalize, warn helper then capture.
- Helper `_warn_bug_as_idea(text, **flags)` builds the suggested `wt add` line.
- No config toggle in v1 (always-on soft warn).
- Tests: CliRunner asserts warn text + idea still created; `--force-idea` silent; other kinds
  silent.

## Alternatives considered

- Guidance-only (skills, no CLI) — rejected (parent AC needs CLI surface).
- Hard redirect / refuse write — rejected (false positives for systemic design bugs).
- Warn also for chore/improvement — rejected (bug-only disposition).

## Acceptance criteria

- [x] `wt idea TEXT --kind bug` prints a soft warn with a suggested `wt add` line and still
      creates the idea.
- [x] `wt idea TEXT --kind bug --force-idea` creates the idea with no warn.
- [x] `--kind improvement|chore|idea` does not warn.
- [x] `wt-capture` skill and WORKFLOW document the fork (actionable → `wt add`; design bug →
      idea with `--force-idea` or without kind).
- [x] No idea↔task repair command; no hard auto-route.

## Test plan

- **Automated:** `tests/test_capture_routing.py` — warn+create; force-idea silent; other kinds
  silent; suggested line includes project/tag when passed. **Executed 2026-07-28:**
  `uv run pytest tests/test_capture_routing.py tests/test_idea_kind.py` — 12 passed.
- **Manual:** capture a bug-shaped line; confirm warn; re-run with `--force-idea`.
- **Regression:** idea capture / kind tests above.

## Rollout / migration

None. Behavior additive at capture time.

## Definition of done

- [x] AC met; tests pass; ledger updated; SPEC-0087 breakdown checked.

## Open questions

(none — IDEA-107 dispositions locked)
