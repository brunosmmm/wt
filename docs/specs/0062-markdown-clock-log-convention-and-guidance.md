---
id: SPEC-0062
title: "Markdown Clock Log convention and guidance"
status: done
owner: user
created: 2026-07-25
updated: 2026-07-25
source_idea: IDEA-074
parent: SPEC-0060
milestone: "M4: cli ergonomics"
tags: [time-tracking, guidance, export]
---

## Context

Second child of [SPEC-0060](./0060-agent-clock-in-clock-out-guidance-for-wt-tracked.md).
[SPEC-0061](./0061-org-side-clock-in-clock-out-primitive.md) shipped the org-side clock
primitive for internal work. This spec adds the markdown-side counterpart: a `## Clock Log`
section for spec files, scaffolded by default, plus guidance telling agents when to use each
side. `scaffold_outbound`/internal `wt spec new` both copy `TEMPLATE.md` verbatim
(`specs.py:scaffold_outbound` — `text = (specs_dir / template_name).read_text()`), so adding
the section to `TEMPLATE.md` once reaches both internal and outbound scaffolds with no further
wiring.

## Decision

Add a `## Clock Log` section to `TEMPLATE.md` (plain `CLOCK-IN: [timestamp]` /
`CLOCK-OUT: [timestamp]` lines, one pair per work session), and add matching guidance to the
global `wt-implement-spec` skill (foreign-repo markdown side) and this repo's `AGENTS.md`
(internal org side, pointing at `wt idea clock-in`/`clock-out`).

## Design

- **`docs/specs/TEMPLATE.md`:** new `## Clock Log` section after `## Test plan`, before
  `## Rollout / migration`. Instructional placeholder text explains the convention and notes
  internal work should prefer `wt idea clock-in`/`clock-out` on the linked idea instead (this
  section is primarily for outbound/foreign-repo implementation work, where org access doesn't
  exist). Not added to `TEMPLATE-epic.md` — epics compose children, each with its own Clock
  Log; not a required section (`OUTBOUND_REQUIRED_SECTIONS`/`REQUIRED_SECTIONS` in
  `tools/spec_lint.py` are unchanged), so existing specs and lint are unaffected.
- **Global `wt-implement-spec` skill** (`~/.claude/skills/wt-implement-spec/SKILL.md`): new
  procedure step — when starting implementation work on a portable spec, append a
  `CLOCK-IN: [timestamp]` line to its `## Clock Log`; when pausing or finishing that session,
  append the matching `CLOCK-OUT: [timestamp]`. Purely a markdown edit — no wt command
  available in a foreign repo (that's the whole reason this side is markdown, not org).
- **This repo's `AGENTS.md`:** new guidance under "While implementing" — for internal
  `SPEC-NNNN` work, run `wt idea clock-in <linked-idea>` when starting, `wt idea clock-out`
  when pausing/finishing.

## Alternatives considered

- **A stricter, machine-parseable markdown format (e.g. a table or YAML block)** — rejected:
  plain `CLOCK-IN:`/`CLOCK-OUT:` lines are trivially greppable/parseable by child 3's
  `pull-clock` (a simple regex, mirroring `_CLOCK_LINE_RE`'s org-side approach) without the
  ceremony of a stricter format; agents write markdown prose easily, tables/YAML less reliably.
- **Scaffolding into `TEMPLATE-epic.md` too** — rejected: epics aren't directly implemented;
  their children are, and each child spec already gets the section via `TEMPLATE.md`.

## Acceptance criteria

- [x] A freshly scaffolded internal spec (`wt spec new`) and outbound spec
      (`scaffold_outbound`) both include an empty `## Clock Log` section.
- [x] `TEMPLATE-epic.md` is unchanged (no Clock Log section).
- [x] `tools/spec_lint.py`'s required-section checks are unaffected — a spec without
      Clock Log content still lints clean (the section is optional content, not a required
      one).
- [x] The global `wt-implement-spec` skill instructs clocking in/out via the markdown Clock Log
      when working a portable spec.
- [x] This repo's `AGENTS.md` instructs clocking in/out via `wt idea clock-in`/`clock-out` for
      internal work.

## Test plan

- **Automated tests** (`tests/test_promote.py`, 4 new tests): scaffolding an internal spec
  (`scaffold_from_idea`) and an outbound spec (`scaffold_outbound`) both produce a `## Clock
  Log` heading; `TEMPLATE-epic.md` scaffolding does not; a scaffolded spec with the section
  left empty (filled elsewhere) still passes `tools/spec_lint.py`'s `validate()` — no new
  required-section regression.
- **Manual verification:** read the diffs to `TEMPLATE.md`, the `wt-implement-spec` skill, and
  `AGENTS.md` for correctness and tone consistency with the surrounding document.
- **Regression guard:** full `uv run pytest` green; existing scaffolded-spec tests (that assert
  on other TEMPLATE.md sections) unaffected by the addition.

## Definition of done

- [x] Acceptance criteria all met.
- [x] Test plan executed; `uv run pytest` green; manual step performed.
- [x] No regressions.
- [x] Spec body matches what shipped.
- [x] `docs/LEDGER.md` regenerated.
